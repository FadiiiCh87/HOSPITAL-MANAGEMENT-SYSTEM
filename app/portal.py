"""Public site and patient/doctor portals. All medical reads enforce ownership."""
import io, os, re, hashlib, smtplib
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from functools import wraps
from xml.sax.saxutils import escape
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from app.extensions import db
from app.models.portal import PatientAccount, DoctorAccount, DoctorSchedule, DoctorUnavailability, Checkup, PublishedReport, AuditEvent, LoginAttempt
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.lab_request import LabRequest
from app.models.laboratory import Laboratory
from app.models.admin import Admin

portal = Blueprint('portal', __name__)
CANCEL_HOURS = 2

def now(): return datetime.now(ZoneInfo('Asia/Riyadh')).replace(tzinfo=None)
def audit(action, target):
    db.session.add(AuditEvent(actor=current_user.get_id() if current_user.is_authenticated else 'guest', action=action, target=str(target)))

def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def inner(*a, **kw):
            if current_user.role not in roles: abort(403)
            return fn(*a, **kw)
        return inner
    return decorator

def doctor_id():
    link = DoctorAccount.query.filter_by(admin_id=current_user.id).first()
    if not link: abort(403)
    return link.doctor_id

def own_appointment(id):
    ap = Appointment.query.filter_by(id=id).with_for_update().first_or_404() if request.method == "POST" else db.get_or_404(Appointment, id)
    if current_user.role == 'Patient' and ap.patient_id != current_user.patient_id: abort(404)
    if current_user.role == 'Doctor' and ap.doctor_id != doctor_id(): abort(404)
    return ap

def safe_next():
    path = request.values.get('next', '')
    return path if path.startswith('/book') and not path.startswith('//') else url_for('portal.patient_dashboard')

def valid_email(value): return len(value)<=100 and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value)
def validate_password(p):
    if len(p)<12 or len(p)>128: raise ValueError('Use a password with 12–128 characters.')

def throttle(label):
    key=hashlib.sha256((label+':'+request.remote_addr).encode()).hexdigest()
    cutoff=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(minutes=15)
    if LoginAttempt.query.filter(LoginAttempt.key==key, LoginAttempt.created_at>cutoff).count()>=10: abort(429)
    db.session.add(LoginAttempt(key=key)); db.session.commit()

def lock_doctor(did):
    # Serialize bookings and schedule changes for a doctor on production PostgreSQL.
    if did and db.engine.dialect.name == 'postgresql':
        db.session.execute(text('SELECT pg_advisory_xact_lock(72418, :doctor)'), {'doctor': did})

def slot_states(did, day, exclude=None):
    clock = now()
    schedule = DoctorSchedule.query.filter_by(doctor_id=did, weekday=day.weekday()).first()
    if not schedule or day < clock.date() or day > clock.date()+timedelta(days=90): return []
    if schedule.slot_minutes <= 0: return []
    appointments = Appointment.query.filter(Appointment.doctor_id==did, Appointment.appointment_date==day, Appointment.status!='Cancelled')
    if exclude: appointments = appointments.filter(Appointment.id!=exclude)
    booked = [(datetime.combine(day,x.appointment_time), datetime.combine(day,x.appointment_time)+timedelta(minutes=x.duration_minutes or 30)) for x in appointments]
    periods = DoctorUnavailability.query.filter(DoctorUnavailability.doctor_id==did, DoctorUnavailability.starts_at < datetime.combine(day+timedelta(days=1),time.min), DoctorUnavailability.ends_at > datetime.combine(day,time.min)).all()
    point = datetime.combine(day,schedule.start_time); end = datetime.combine(day,schedule.end_time)
    states = []
    while point+timedelta(minutes=schedule.slot_minutes) <= end:
        finish = point+timedelta(minutes=schedule.slot_minutes)
        status = 'Available'
        if point <= clock: status = 'Time passed'
        elif any(point < p.ends_at and finish > p.starts_at for p in periods): status = 'Not available'
        elif any(point < finish_at and finish > start_at for start_at, finish_at in booked): status = 'Booked'
        states.append({'time': point.strftime('%H:%M'), 'status': status})
        point = finish
    return states

def available(did, day, exclude=None):
    return [s['time'] for s in slot_states(did,day,exclude) if s['status']=='Available']

def availability_message(did, day):
    if day < now().date(): return 'This date has passed. Choose a future date.'
    if day > now().date()+timedelta(days=90): return 'Bookings open up to 90 days ahead.'
    if not DoctorSchedule.query.filter_by(doctor_id=did).first(): return 'This doctor has not published working hours yet. Please contact reception.'
    if not DoctorSchedule.query.filter_by(doctor_id=did,weekday=day.weekday()).first(): return 'This doctor does not have working hours on this weekday. Choose another day.'
    return 'No bookable slots remain on this date. Unavailable, booked and past times are shown below.'

@portal.get('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('portal.patient_dashboard' if current_user.role=='Patient' else 'portal.doctor_dashboard' if current_user.role=='Doctor' else 'auth.dashboard'))
    return render_template('portal/home.html', departments=Department.query.order_by(Department.name).all(),doctors=Doctor.query.order_by(Doctor.full_name).all(),schedules=DoctorSchedule.query.order_by(DoctorSchedule.weekday).all())

@portal.route('/patient/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        throttle('register')
        try:
            email=request.form.get('email','').strip().lower(); name=request.form.get('name','').strip(); password=request.form.get('password','')
            validate_password(password)
            if not valid_email(email) or not name or len(name)>100: raise ValueError('Enter a valid name and email.')
            if PatientAccount.query.filter_by(email=email).first() or Patient.query.filter_by(email=email).first():
                raise ValueError('This email is already registered. Sign in or contact reception to verify your existing record.')
            patient=Patient(full_name=name,email=email,phone=request.form.get('phone','')[:20])
            db.session.add(patient); db.session.flush()
            account=PatientAccount(patient_id=patient.id,email=email,password=generate_password_hash(password))
            db.session.add(account); db.session.commit(); login_user(account)
            audit('patient_registered',patient.id); db.session.commit()
            return redirect(safe_next())
        except (ValueError,IntegrityError) as e:
            db.session.rollback();flash(str(e) if isinstance(e,ValueError) else 'Account could not be created. Try signing in.','danger')
    return render_template('portal/account.html',mode='register',next=safe_next())

@portal.route('/patient/login',methods=['GET','POST'])
def patient_login():
    if request.method=='POST':
        throttle('patient-login')
        user=PatientAccount.query.filter_by(email=request.form.get('email','').strip().lower()).first()
        if user and check_password_hash(user.password,request.form.get('password','')):
            login_user(user);audit('login',user.patient_id);db.session.commit();return redirect(safe_next())
        flash('Invalid email or password.','danger')
    return render_template('portal/account.html',mode='login',next=safe_next())

@portal.post('/patient/logout')
@login_required
def patient_logout():
    logout_user();return redirect(url_for('portal.home'))

@portal.route('/patient/profile',methods=['GET','POST'])
@require_role('Patient')
def profile():
    if request.method=='POST':
        p=current_user.patient
        name=request.form.get('name','').strip()
        if not name or len(name)>100: abort(400)
        p.full_name=name;p.phone=request.form.get('phone','')[:20];p.address=request.form.get('address','')[:1000]
        if request.form.get('password'):
            if not check_password_hash(current_user.password,request.form.get('current_password','')): abort(400)
            try:validate_password(request.form['password'])
            except ValueError as e:flash(str(e),'danger');return redirect(url_for('portal.profile'))
            current_user.password=generate_password_hash(request.form['password']);current_user.token_version+=1
            login_user(current_user)
        audit('profile_updated',p.id);db.session.commit();flash('Profile saved.','success')
    return render_template('portal/account.html',mode='profile')

@portal.route('/patient/reset',methods=['GET','POST'])
def reset_request():
    if request.method=='POST':
        throttle('reset')
        user=PatientAccount.query.filter_by(email=request.form.get('email','').lower().strip()).first()
        if not os.getenv('SMTP_HOST'):
            flash('Email recovery is not configured. Contact reception for identity-verified account recovery.','warning')
        else:
            if user:
                token=URLSafeTimedSerializer(current_app.secret_key).dumps({'id':user.id,'version':user.token_version},salt='patient-reset')
                base_url=os.getenv('PUBLIC_BASE_URL') or os.getenv('RENDER_EXTERNAL_URL') or 'https://hospital-management-system-fahad.onrender.com'
                link=base_url.rstrip('/')+url_for('portal.reset_password',token=token)
                msg=EmailMessage();msg['Subject']='Reset your hospital portal password';msg['From']=os.environ['SMTP_FROM'];msg['To']=user.email;msg.set_content('This link expires in 30 minutes:\n'+link)
                try:
                    with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','587')),timeout=10) as smtp:
                        smtp.starttls();smtp.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD']);smtp.send_message(msg)
                except Exception: current_app.logger.error('Password recovery email delivery failed')
            flash('If the account exists, a recovery email has been requested.','info')
    return render_template('portal/account.html',mode='reset')

@portal.route('/patient/reset/<token>',methods=['GET','POST'])
def reset_password(token):
    try:
        payload=URLSafeTimedSerializer(current_app.secret_key).loads(token,salt='patient-reset',max_age=1800)
        user=db.session.get(PatientAccount,payload['id'])
        if not user or user.token_version!=payload['version']:abort(400)
    except (BadSignature,SignatureExpired,KeyError):abort(400)
    if request.method=='POST':
        try:validate_password(request.form.get('password',''))
        except ValueError as e:flash(str(e),'danger');return render_template('portal/account.html',mode='new-password')
        user.password=generate_password_hash(request.form['password']);user.token_version+=1;db.session.commit();flash('Password changed. Please sign in.','success');return redirect(url_for('portal.patient_login'))
    return render_template('portal/account.html',mode='new-password')

@portal.route('/book',methods=['GET','POST'])
def book():
    did=request.values.get('doctor',type=int); doctor=db.session.get(Doctor,did) if did else None
    raw=request.values.get('date',now().date().isoformat())
    try:day=date.fromisoformat(raw)
    except ValueError:abort(400)
    if request.method=='POST' and doctor: lock_doctor(did)
    slots=available(did,day) if doctor else []
    if request.method=='POST':
        if not current_user.is_authenticated:
            session['pending_booking']={'doctor':did,'date':day.isoformat(),'time':request.form.get('time',''),'reason':request.form.get('reason','')[:2000]}
            return redirect(url_for('portal.patient_login',next='/book?doctor='+str(did)+'&date='+day.isoformat()))
        if current_user.role!='Patient':abort(403)
        slot=request.form.get('time','')
        if slot not in slots:flash('That slot is unavailable. Choose another.','warning')
        else:
            ap=Appointment(duration_minutes=DoctorSchedule.query.filter_by(doctor_id=did,weekday=day.weekday()).first().slot_minutes,patient_id=current_user.patient_id,doctor_id=did,appointment_date=day,appointment_time=time.fromisoformat(slot),reason=request.form.get('reason','')[:2000],status='Confirmed')
            try:
                db.session.add(ap);db.session.flush();audit('appointment_booked',ap.id);db.session.commit();session.pop('pending_booking',None);flash(f'Appointment #{ap.id} confirmed.','success');return redirect(url_for('portal.patient_dashboard'))
            except IntegrityError:db.session.rollback();flash('Another booking just reserved that slot. Choose a new slot.','warning')
    return render_template('portal/book.html',doctors=Doctor.query.order_by(Doctor.full_name).all(),doctor=doctor,day=day,slots=slots,slot_states=slot_states(did,day) if doctor else [],availability_message=availability_message(did,day) if doctor else '',minimum=now().date(),maximum=now().date()+timedelta(days=90),pending=session.get('pending_booking',{}))

@portal.get('/patient/dashboard')
@require_role('Patient')
def patient_dashboard():
    appointments=Appointment.query.filter_by(patient_id=current_user.patient_id).order_by(Appointment.appointment_date.desc(),Appointment.appointment_time.desc()).all()
    prescriptions=Prescription.query.filter_by(patient_id=current_user.patient_id).order_by(Prescription.prescription_date.desc()).all()
    reports=PublishedReport.query.join(LabRequest).filter(LabRequest.patient_id==current_user.patient_id,PublishedReport.published_at.isnot(None)).order_by(PublishedReport.published_at.desc()).all()
    lab_requests=LabRequest.query.filter_by(patient_id=current_user.patient_id).order_by(LabRequest.request_date.desc()).all()
    checkups=Checkup.query.join(Appointment).filter(Appointment.patient_id==current_user.patient_id).all()
    since=request.args.get('from','');until=request.args.get('to','')
    def in_range(d):return (not since or d.isoformat()>=since) and (not until or d.isoformat()<=until)
    timeline=[(a.appointment_date,'Appointment',f'#{a.id} · {a.doctor.full_name} · {a.status}') for a in appointments]+[(p.prescription_date,'Prescription',p.diagnosis) for p in prescriptions]+[(r.published_at.date(),'Test report',r.lab_request.laboratory.test_name) for r in reports]+[(c.appointment.appointment_date,'Checkup',c.diagnosis) for c in checkups]
    timeline=sorted([x for x in timeline if in_range(x[0])],key=lambda x:x[0],reverse=True)
    upcoming=[a for a in appointments if datetime.combine(a.appointment_date,a.appointment_time)>now() and a.status in ('Pending','Confirmed')]
    upcoming.sort(key=lambda a:(a.appointment_date,a.appointment_time))
    audit('medical_history_viewed',current_user.patient_id);db.session.commit()
    return render_template('portal/dashboard.html',appointments=appointments,prescriptions=prescriptions,reports=reports,lab_requests=lab_requests,checkups=checkups,timeline=timeline,upcoming=upcoming,availability_warnings=[ap.id for ap in appointments if ap.status in ('Pending','Confirmed') and datetime.combine(ap.appointment_date,ap.appointment_time)>now() and ap.appointment_time.strftime('%H:%M') not in available(ap.doctor_id,ap.appointment_date,ap.id)],clock=now(),since=since,until=until)

@portal.post('/patient/appointments/<int:id>/cancel')
@require_role('Patient')
def cancel(id):
    ap=own_appointment(id)
    if ap.status not in ('Pending','Confirmed') or datetime.combine(ap.appointment_date,ap.appointment_time)<now()+timedelta(hours=CANCEL_HOURS):abort(400)
    ap.status='Cancelled';audit('appointment_cancelled',id);db.session.commit();flash('Appointment cancelled.','success');return redirect(url_for('portal.patient_dashboard'))

@portal.route('/patient/appointments/<int:id>/reschedule',methods=['GET','POST'])
@require_role('Patient')
def reschedule(id):
    ap=own_appointment(id)
    if ap.status not in ('Pending','Confirmed') or datetime.combine(ap.appointment_date,ap.appointment_time)<now()+timedelta(hours=CANCEL_HOURS):abort(400)
    try:day=date.fromisoformat(request.values.get('date',ap.appointment_date.isoformat()))
    except ValueError:abort(400)
    if request.method=='POST': lock_doctor(ap.doctor_id)
    slots=available(ap.doctor_id,day,ap.id)
    if request.method=='POST':
        if request.form.get('time') not in slots:abort(409)
        ap.appointment_date=day;ap.appointment_time=time.fromisoformat(request.form['time']);ap.duration_minutes=DoctorSchedule.query.filter_by(doctor_id=ap.doctor_id,weekday=day.weekday()).first().slot_minutes;ap.status='Confirmed'
        try:audit('appointment_rescheduled',id);db.session.commit()
        except IntegrityError:db.session.rollback();abort(409)
        flash('Appointment rescheduled.','success');return redirect(url_for('portal.patient_dashboard'))
    return render_template('portal/book.html',doctors=[ap.doctor],doctor=ap.doctor,day=day,slots=slots,slot_states=slot_states(ap.doctor_id,day,ap.id),availability_message=availability_message(ap.doctor_id,day),reschedule=ap,minimum=now().date(),maximum=now().date()+timedelta(days=90),pending=session.get('pending_booking',{}))

def pdf_document(title,lines,filename):
    out=io.BytesIO();styles=getSampleStyleSheet();story=[Paragraph(escape(title),styles['Title']),Spacer(1,18)]
    for label,value in lines:
        story+=[Paragraph('<b>'+escape(label)+'</b>: '+escape(str(value or '—')).replace('\n','<br/>'),styles['BodyText']),Spacer(1,10)]
    SimpleDocTemplate(out).build(story);out.seek(0)
    return send_file(out,mimetype='application/pdf',as_attachment=True,download_name=filename)

@portal.get('/patient/prescriptions/<int:id>.pdf')
@require_role('Patient')
def prescription_pdf(id):
    p=Prescription.query.filter_by(id=id,patient_id=current_user.patient_id).first_or_404();audit('prescription_downloaded',id);db.session.commit()
    return pdf_document('Prescription', [('Patient',p.patient.full_name),('Date',p.prescription_date),('Doctor',p.doctor.full_name),('Diagnosis',p.diagnosis),('Medicines',p.medicines),('Notes',p.notes)],f'prescription-{id}.pdf')

@portal.get('/patient/reports/<int:id>.pdf')
@require_role('Patient')
def report_pdf(id):
    r=PublishedReport.query.join(LabRequest).filter(PublishedReport.id==id,PublishedReport.published_at.isnot(None),LabRequest.patient_id==current_user.patient_id).first_or_404()
    audit('report_downloaded',id);db.session.commit()
    if r.file_data:return send_file(io.BytesIO(r.file_data),mimetype='application/pdf',as_attachment=True,download_name=f'report-{id}.pdf')
    l=r.lab_request
    return pdf_document('Laboratory report',[('Patient',l.patient.full_name),('Test',l.laboratory.test_name),('Requested',l.request_date),('Published',r.published_at),('Result',l.result)],f'report-{id}.pdf')

@portal.get('/doctor/dashboard')
@require_role('Doctor','Admin')
def doctor_dashboard():
    q=Appointment.query
    if current_user.role=='Doctor':q=q.filter_by(doctor_id=doctor_id())
    return render_template('portal/doctor.html',appointments=q.order_by(Appointment.appointment_date.desc()).all())

@portal.route('/doctor/appointments/<int:id>',methods=['GET','POST'])
@require_role('Doctor','Admin')
def consultation(id):
    ap=own_appointment(id);checkup=Checkup.query.filter_by(appointment_id=id).first()
    if ap.status=='Cancelled':abort(400)
    if request.method=='POST':
        diagnosis=request.form.get('diagnosis','').strip();medicines=request.form.get('medicines','').strip()
        if not diagnosis or not medicines:abort(400)
        follow=request.form.get('follow_up')
        try:follow=date.fromisoformat(follow) if follow else None
        except ValueError:abort(400)
        if not checkup:checkup=Checkup(appointment_id=id);db.session.add(checkup)
        checkup.diagnosis=diagnosis[:5000];checkup.notes=request.form.get('notes','')[:5000];checkup.follow_up=follow
        rx=db.session.get(Prescription,checkup.prescription_id) if checkup.prescription_id else None
        if not rx:
            rx=Prescription(patient_id=ap.patient_id,doctor_id=ap.doctor_id,prescription_date=now().date());db.session.add(rx)
        rx.diagnosis=checkup.diagnosis;rx.medicines=medicines[:5000];rx.notes=checkup.notes
        db.session.flush();checkup.prescription_id=rx.id
        ap.status='Completed';audit('checkup_saved',id);db.session.commit();flash('Checkup and prescription saved.','success');return redirect(url_for('portal.doctor_dashboard'))
    audit('doctor_patient_history_viewed',ap.patient_id);db.session.commit()
    return render_template('portal/consultation.html',appointment=ap,checkup=checkup,laboratory_tests=Laboratory.query.order_by(Laboratory.test_name).all(),prescriptions=Prescription.query.filter_by(patient_id=ap.patient_id).order_by(Prescription.prescription_date.desc()).all(),reports=PublishedReport.query.join(LabRequest).filter(LabRequest.patient_id==ap.patient_id,PublishedReport.published_at.isnot(None)).all())

@portal.route('/admin/portal',methods=['GET','POST'])
@require_role('Admin')
def admin_portal():
    if request.method=='POST':
        action=request.form.get('action')
        try:
            if action=='schedule':
                did=int(request.form['doctor']);db.get_or_404(Doctor,did);lock_doctor(did);weekday=int(request.form['weekday']);minutes=int(request.form['minutes']);start=time.fromisoformat(request.form['start']);end=time.fromisoformat(request.form['end'])
                if weekday not in range(7) or minutes not in (15,20,30,45,60) or start>=end or datetime.combine(date.today(),start)+timedelta(minutes=minutes)>datetime.combine(date.today(),end):raise ValueError('Invalid schedule.')
                s=DoctorSchedule.query.filter_by(doctor_id=did,weekday=weekday).first() or DoctorSchedule(doctor_id=did,weekday=weekday)
                s.start_time=start;s.end_time=end;s.slot_minutes=minutes;db.session.add(s);audit('schedule_updated',did)
            elif action=='doctor_account':
                did=int(request.form['doctor']);db.get_or_404(Doctor,did);email=request.form['email'].lower().strip();password=request.form['password'];validate_password(password)
                if not valid_email(email):raise ValueError('Invalid email.')
                a=Admin(full_name=db.session.get(Doctor,did).full_name,email=email,password=generate_password_hash(password),role='Doctor');db.session.add(a);db.session.flush();db.session.add(DoctorAccount(admin_id=a.id,doctor_id=did));audit('doctor_account_created',did)
            elif action=='enroll':
                patient=db.get_or_404(Patient,int(request.form['patient']));email=request.form.get('email','').strip().lower();password=request.form['password'];validate_password(password)
                if request.form.get('verified')!='yes' or not valid_email(email):raise ValueError('Verify patient identity and enter a valid email.')
                db.session.add(PatientAccount(patient_id=patient.id,email=email,password=generate_password_hash(password)));audit('identity_verified_patient_enrollment',patient.id)
            elif action=='recover':
                account=db.get_or_404(PatientAccount,int(request.form['account']));validate_password(request.form['password'])
                if request.form.get('verified')!='yes':raise ValueError('Verify patient identity before recovery.')
                account.password=generate_password_hash(request.form['password']);account.token_version+=1;audit('identity_verified_password_recovery',account.patient_id)
            else:abort(400)
            db.session.commit();flash('Saved successfully.','success')
        except (ValueError,KeyError,IntegrityError) as e:db.session.rollback();flash(str(e) if isinstance(e,ValueError) else 'Duplicate account or invalid input.','danger')
        return redirect(url_for('portal.admin_portal'))
    return render_template('portal/admin.html',doctors=Doctor.query.order_by(Doctor.full_name).all(),schedules=DoctorSchedule.query.all(),accounts=PatientAccount.query.all(),patients=Patient.query.all(),events=AuditEvent.query.order_by(AuditEvent.id.desc()).limit(100).all())

@portal.route('/admin/reports/<int:id>/publish',methods=['GET','POST'])
@require_role('Admin','Lab Staff')
def publish_report(id):
    lab=db.get_or_404(LabRequest,id);r=PublishedReport.query.filter_by(lab_request_id=id).first()
    if request.method=='POST':
        if not r:r=PublishedReport(lab_request_id=id);db.session.add(r)
        upload=request.files.get('file')
        if upload and upload.filename:
            contents=upload.read()
            if not contents.startswith(b'%PDF-') or len(contents)>4*1024*1024:abort(400)
            r.file_data=contents
        if request.form.get('action')=='publish':
            if lab.status!='Completed' or not lab.result:flash('Complete the laboratory result before publishing.','warning');db.session.rollback();return redirect(request.path)
            r.published_at=now();audit('report_published',id)
        else:r.published_at=None;audit('report_unpublished',id)
        db.session.commit();flash('Report publication updated.','success')
    return render_template('portal/publish.html',lab=lab,report=r)


@portal.post('/doctor/appointments/<int:id>/request-test')
@require_role('Doctor')
def request_test(id):
    ap = own_appointment(id)
    if ap.status == 'Cancelled': abort(400)
    test = db.get_or_404(Laboratory, request.form.get('laboratory_id', type=int))
    lab = LabRequest(patient_id=ap.patient_id, doctor_id=ap.doctor_id, laboratory_id=test.id, request_date=now().date(), status='Pending')
    db.session.add(lab)
    db.session.flush()
    audit('test_requested', lab.id)
    db.session.commit()
    flash('Laboratory test requested.', 'success')
    return redirect(url_for('portal.consultation', id=ap.id))


@portal.route('/staff/availability', methods=['GET','POST'])
@require_role('Admin','Doctor')
def manage_availability():
    doctors = Doctor.query.order_by(Doctor.full_name).all() if current_user.role=='Admin' else [db.get_or_404(Doctor,doctor_id())]
    did = request.values.get('doctor', type=int)
    if current_user.role=='Doctor':
        own = doctor_id()
        if did and did != own: abort(403)
        did = own
    elif not did and doctors: did = doctors[0].id
    selected = db.get_or_404(Doctor,did) if did else None
    if request.method=='POST':
        if not selected: abort(400)
        lock_doctor(did)
        try:
            action = request.form.get('action')
            if action=='schedule':
                weekdays = [int(x) for x in request.form.getlist('weekdays')]
                start = time.fromisoformat(request.form['start']); end = time.fromisoformat(request.form['end']); minutes = int(request.form['minutes'])
                if not weekdays or any(x not in range(7) for x in weekdays) or start>=end or minutes not in (15,20,30,45,60) or datetime.combine(date.today(),start)+timedelta(minutes=minutes)>datetime.combine(date.today(),end): raise ValueError('Choose working days and valid hours with at least one complete slot.')
                for weekday in set(weekdays):
                    schedule=DoctorSchedule.query.filter_by(doctor_id=did,weekday=weekday).first() or DoctorSchedule(doctor_id=did,weekday=weekday)
                    schedule.start_time=start;schedule.end_time=end;schedule.slot_minutes=minutes;db.session.add(schedule)
                audit('weekly_availability_updated',did)
            elif action=='remove_day':
                weekday=int(request.form['weekday'])
                if weekday not in range(7): raise ValueError('Invalid weekday.')
                DoctorSchedule.query.filter_by(doctor_id=did,weekday=weekday).delete()
                audit('working_day_removed',did)
            elif action=='unavailable':
                start=datetime.fromisoformat(request.form['starts_at']);end=datetime.fromisoformat(request.form['ends_at'])
                if start.tzinfo or end.tzinfo or start>=end or end<=now(): raise ValueError('Choose a valid future unavailability period in Saudi Arabia time.')
                reason=request.form.get('reason','Unavailable').strip()[:200] or 'Unavailable'
                db.session.add(DoctorUnavailability(doctor_id=did,starts_at=start,ends_at=end,reason=reason))
                audit('doctor_unavailability_added',did)
            elif action=='remove_unavailable':
                period=db.get_or_404(DoctorUnavailability,request.form.get('period',type=int))
                if period.doctor_id!=did: abort(403)
                db.session.delete(period);audit('doctor_unavailability_removed',did)
            else: abort(400)
            db.session.commit()
            flash('Availability saved. Review affected bookings below; existing appointments were not cancelled.', 'success')
        except (ValueError,KeyError):
            db.session.rollback();flash('Invalid dates, days or hours. End time must follow start time.', 'danger')
        return redirect(url_for('portal.manage_availability',doctor=did))
    schedules=DoctorSchedule.query.filter_by(doctor_id=did).order_by(DoctorSchedule.weekday).all() if selected else []
    periods=DoctorUnavailability.query.filter_by(doctor_id=did).filter(DoctorUnavailability.ends_at>now()).order_by(DoctorUnavailability.starts_at).all() if selected else []
    upcoming=Appointment.query.filter(Appointment.doctor_id==did,Appointment.appointment_date>=now().date(),Appointment.status.in_(['Pending','Confirmed'])).all() if selected else []
    affected=[ap for ap in upcoming if datetime.combine(ap.appointment_date,ap.appointment_time)>now() and ap.appointment_time.strftime('%H:%M') not in available(did,ap.appointment_date,ap.id)]
    return render_template('portal/availability.html',doctors=doctors,selected=selected,schedules=schedules,periods=periods,affected=affected)
