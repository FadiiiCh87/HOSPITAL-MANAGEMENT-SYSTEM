import io, re, tempfile, unittest, os
from datetime import timedelta, time, datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.laboratory import Laboratory
from app.models.lab_request import LabRequest
from app.models.portal import *
from app.portal import now

class PortalTests(unittest.TestCase):
    def setUp(self):
        f=tempfile.NamedTemporaryFile(delete=False);self.path=f.name;f.close()
        self.app=create_app({'TESTING':True,'CLINICAL_ADMIN_IDS':'1','SECRET_KEY':'test-secret','SQLALCHEMY_DATABASE_URI':'sqlite:///'+self.path,'SQLALCHEMY_ENGINE_OPTIONS':{},'WTF_CSRF_ENABLED':False,'SESSION_COOKIE_SECURE':False})
        self.client=self.app.test_client();self.day=now().date()+timedelta(days=3)
        with self.app.app_context():
            db.create_all()
            db.session.add(Department(name='Cardiology'));db.session.flush()
            db.session.add_all([Doctor(full_name='Dr One',email='one@clinic.test',department_id=1),Doctor(full_name='Dr Two',email='two@clinic.test',department_id=1)])
            db.session.add_all([Admin(full_name='Admin',email='admin@clinic.test',password=generate_password_hash('test-password-123'),role='Admin'),Admin(full_name='Dr One',email='doctor@clinic.test',password=generate_password_hash('test-password-123'),role='Doctor')]);db.session.flush()
            db.session.add(DoctorAccount(admin_id=2,doctor_id=1))
            db.session.add(DoctorSchedule(doctor_id=1,weekday=self.day.weekday(),start_time=time(9),end_time=time(12),slot_minutes=30))
            db.session.add_all([Patient(full_name='Alice',email='alice@test.com'),Patient(full_name='Bob',email='bob@test.com')]);db.session.flush()
            db.session.add_all([PatientAccount(patient_id=1,email='alice@test.com',password=generate_password_hash('test-password-123')),PatientAccount(patient_id=2,email='bob@test.com',password=generate_password_hash('test-password-123'))])
            db.session.add(Laboratory(test_name='Blood test',category='Hematology',price=10));db.session.flush()
            db.session.add_all([Appointment(patient_id=1,doctor_id=1,appointment_date=self.day,appointment_time=time(9),status='Confirmed'),Appointment(patient_id=2,doctor_id=2,appointment_date=self.day,appointment_time=time(9),status='Confirmed')]);db.session.flush()
            db.session.add_all([Prescription(patient_id=2,doctor_id=2,diagnosis='PRIVATE-BOB-DIAGNOSIS',medicines='SECRET-BOB-MEDICINE',prescription_date=self.day),LabRequest(patient_id=1,doctor_id=1,laboratory_id=1,request_date=self.day,status='Completed',result='DRAFT-SECRET')]);db.session.flush()
            db.session.add(PublishedReport(lab_request_id=1));db.session.commit()
    def tearDown(self):
        with self.app.app_context():db.session.remove();db.drop_all()
        os.unlink(self.path)
    def login(self,who='alice'):
        path='/staff/login' if who in ('admin','doctor') else '/patient/login'
        email=who+'@clinic.test' if who in ('admin','doctor') else who+'@test.com'
        return self.client.post(path,data={'email':email,'password':'test-password-123'},follow_redirects=True)
    def test_guest_and_registration_preserve_booking(self):
        self.assertEqual(self.client.get('/').status_code,200)
        r=self.client.post('/book',data={'doctor':1,'date':str(self.day),'time':'09:30','reason':'Preserved reason'})
        self.assertEqual(r.status_code,302)
        r=self.client.post('/patient/register',data={'name':'New Patient','email':'new@test.com','password':'test-password-123','next':f'/book?doctor=1&date={self.day}'},follow_redirects=True)
        self.assertIn(b'Preserved reason',r.data);self.assertIn(b'selected>09:30',r.data)
    def test_patient_can_switch_to_staff_without_forbidden(self):
        self.login()
        response = self.client.get("/staff/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Enter valid staff credentials", response.data)
        response = self.client.post("/staff/login", data={"email":"admin@clinic.test", "password":"wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/patient/dashboard").status_code, 200)
        response = self.login("admin")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/admin/portal").status_code, 200)
        self.assertEqual(self.client.get("/patient/dashboard").status_code, 403)

    def test_patient_isolation_and_staff_denial(self):
        self.assertEqual(self.login().status_code,200)
        r=self.client.get('/patient/dashboard');self.assertNotIn(b'PRIVATE-BOB',r.data);self.assertNotIn(b'SECRET-BOB',r.data)
        for path in ['/dashboard','/patients','/appointments','/admin/portal','/doctor/dashboard']:
            self.assertEqual(self.client.get(path).status_code,403,path)
        self.assertEqual(self.client.get('/patient/prescriptions/1.pdf').status_code,404)
        self.assertEqual(self.client.post('/patient/appointments/2/cancel').status_code,404)
    def test_book_cancel_rebook_reschedule(self):
        self.login()
        data={'doctor':1,'date':str(self.day),'time':'09:30','reason':'Visit'}
        self.assertEqual(self.client.post('/book',data=data,follow_redirects=True).status_code,200)
        with self.app.app_context():self.assertEqual(Appointment.query.count(),3)
        self.client.post('/book',data=data)
        with self.app.app_context():self.assertEqual(Appointment.query.count(),3)
        self.assertEqual(self.client.post('/patient/appointments/3/cancel').status_code,302)
        self.client.post('/book',data=data)
        self.assertEqual(self.client.post('/patient/appointments/4/reschedule',data={'date':str(self.day),'time':'10:00'}).status_code,302)
        with self.app.app_context():self.assertEqual(db.session.get(Appointment,4).appointment_time,time(10))
    def test_atomic_duplicate_constraint(self):
        with self.app.app_context():
            db.session.add(Appointment(patient_id=2,doctor_id=1,appointment_date=self.day,appointment_time=time(9),status='Pending'))
            with self.assertRaises(IntegrityError):db.session.commit()
            db.session.rollback()

    def login_reception(self):
        with self.app.app_context():
            db.session.add(Admin(full_name='Reception', email='reception@clinic.test', password=generate_password_hash('test-password-123'), role='Receptionist'))
            db.session.commit()
        self.client.post('/patient/logout')
        return self.client.post('/staff/login', data={'email':'reception@clinic.test','password':'test-password-123'})

    def test_online_request_reception_confirms_patient_sees_instructions(self):
        self.login()
        page = self.client.post('/book', data={'doctor':1,'date':str(self.day),'time':'09:30','status':'Confirmed'}, follow_redirects=True)
        self.assertIn(b'Awaiting confirmation', page.data)
        with self.app.app_context():
            self.assertEqual(db.session.get(Appointment,3).status,'Pending')
        self.assertNotIn(b'15 minutes', page.data.split(b'Awaiting reception confirmation')[1].split(b'</td>')[0])
        self.login_reception()
        page=self.client.get('/appointments?status=Pending')
        self.assertIn(b'Confirm</button>',page.data);self.assertIn(b'Reject</button>',page.data)
        self.assertEqual(self.client.post('/appointments/3/review',data={'decision':'Confirmed'}).status_code,302)
        self.assertEqual(self.client.post('/appointments/3/review',data={'decision':'Rejected'}).status_code,409)
        self.client.get('/logout');self.login()
        page=self.client.get('/patient/dashboard')
        self.assertIn(b'collect your booking receipt from reception',page.data)
        self.assertIn(b'arrive 15 minutes before your appointment',page.data)
        self.assertEqual(self.client.get('/patient/appointments/status').json['3'],'Confirmed')

    def test_rejected_request_releases_slot_and_preserves_history(self):
        self.login()
        data={'doctor':1,'date':str(self.day),'time':'09:30'}
        self.client.post('/book',data=data)
        self.login_reception()
        self.assertEqual(self.client.post('/appointments/3/review',data={'decision':'Rejected'}).status_code,302)
        self.client.get('/logout');self.login()
        self.assertIn(b'Reception rejected this booking request',self.client.get('/patient/dashboard').data)
        self.client.post('/book',data=data)
        with self.app.app_context():
            self.assertEqual(db.session.get(Appointment,3).status,'Rejected')
            self.assertEqual(db.session.get(Appointment,4).status,'Pending')

    def test_review_requires_staff_csrf_and_valid_pending_request(self):
        self.login()
        self.client.post('/book',data={'doctor':1,'date':str(self.day),'time':'09:30'})
        self.assertEqual(self.client.post('/appointments/3/review',data={'decision':'Confirmed'}).status_code,403)
        self.client.post('/patient/logout');self.login('doctor')
        self.assertEqual(self.client.post('/appointments/3/review',data={'decision':'Confirmed'}).status_code,403)
        self.client.get('/logout');self.login_reception()
        self.assertIn(self.client.get('/appointments/3/review').status_code,(403,405))
        self.assertEqual(self.client.post('/appointments/3/review',data={'decision':'Completed'}).status_code,400)
        self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post('/appointments/3/review',data={'decision':'Confirmed'}).status_code,400)

    def test_reception_cannot_confirm_unavailable_request(self):
        self.login()
        self.client.post('/book',data={'doctor':1,'date':str(self.day),'time':'09:30'})
        with self.app.app_context():
            db.session.add(DoctorUnavailability(doctor_id=1,starts_at=datetime.combine(self.day,time(9,30)),ends_at=datetime.combine(self.day,time(10)),reason='Private leave'))
            db.session.commit()
        self.login_reception()
        page=self.client.post('/appointments/3/review',data={'decision':'Confirmed'},follow_redirects=True)
        self.assertIn(b'no longer available',page.data)
        with self.app.app_context():self.assertEqual(db.session.get(Appointment,3).status,'Pending')

    def test_reschedule_requires_new_approval_and_status_endpoint_is_private(self):
        self.login()
        self.assertEqual(self.client.post('/patient/appointments/1/reschedule',data={'date':str(self.day),'time':'10:00'}).status_code,302)
        with self.app.app_context():self.assertEqual(db.session.get(Appointment,1).status,'Pending')
        statuses=self.client.get('/patient/appointments/status')
        self.assertEqual(statuses.json,{'1':'Pending'})
        self.assertIn('no-store',statuses.headers['Cache-Control'])
        self.client.post('/patient/logout');self.login('bob')
        self.assertEqual(self.client.get('/patient/appointments/status').json,{'2':'Confirmed'})
    def test_draft_report_publish_pdf_and_withdraw(self):
        self.login();self.assertNotIn(b'DRAFT-SECRET',self.client.get('/patient/dashboard').data)
        self.assertEqual(self.client.get('/patient/reports/1.pdf').status_code,404)
        self.client.post('/patient/logout');self.login('admin')
        r=self.client.post('/admin/reports/1/publish',data={'action':'publish','file':(io.BytesIO(b'%PDF-1.4\nTEST-REPORT'),'report.pdf')},content_type='multipart/form-data');self.assertEqual(r.status_code,200)
        self.client.post('/patient/logout');self.login()
        self.assertIn(b'DRAFT-SECRET',self.client.get('/patient/dashboard').data)
        self.assertTrue(self.client.get('/patient/reports/1.pdf').data.startswith(b'%PDF-'))
        self.client.post('/patient/logout');self.login('admin');self.client.post('/admin/reports/1/publish',data={'action':'draft'})
        self.client.post('/patient/logout');self.login();self.assertEqual(self.client.get('/patient/reports/1.pdf').status_code,404)
    def test_doctor_access_checkup_prescription_and_followup(self):
        self.login('doctor')
        self.assertEqual(self.client.get('/doctor/appointments/2').status_code,404)
        self.assertEqual(self.client.get('/patients').status_code,403)
        data={'diagnosis':'Test diagnosis','medicines':'Medicine A','notes':'Checkup notes','follow_up':str(self.day+timedelta(days=7))}
        self.assertEqual(self.client.post('/doctor/appointments/1',data=data).status_code,302)
        self.client.post('/doctor/appointments/1',data=data)
        with self.app.app_context():self.assertEqual(Checkup.query.count(),1);self.assertEqual(Prescription.query.filter_by(patient_id=1).count(),1)
        self.client.post('/patient/logout');self.login()
        r=self.client.get('/patient/dashboard');self.assertIn(b'Test diagnosis',r.data);self.assertIn(b'Checkup notes',r.data)
        self.assertTrue(self.client.get('/patient/prescriptions/2.pdf').data.startswith(b'%PDF-'))
    def test_cancel_cutoff(self):
        with self.app.app_context():
            ap=db.session.get(Appointment,1);n=now()+timedelta(hours=1);ap.appointment_date=n.date();ap.appointment_time=n.time();db.session.commit()
        self.login();self.assertEqual(self.client.post('/patient/appointments/1/cancel').status_code,400)
    def test_reset_invalidates_old_sessions(self):
        self.login();other=self.app.test_client()
        other.post('/staff/login',data={'email':'admin@clinic.test','password':'test-password-123'})
        r=other.post('/admin/portal',data={'action':'recover','account':1,'password':'new-password-123','verified':'yes'});self.assertEqual(r.status_code,302)
        self.assertEqual(self.client.get('/patient/dashboard').status_code,302)
    def test_csrf_and_private_cache(self):
        self.app.config['WTF_CSRF_ENABLED']=True
        self.assertEqual(self.client.post('/patient/login',data={'email':'alice@test.com','password':'test-password-123'}).status_code,400)
        r=self.client.get('/patient/login');token=re.search(rb'name="csrf_token" value="([^"]+)"',r.data).group(1).decode()
        r=self.client.post('/patient/login',data={'csrf_token':token,'email':'alice@test.com','password':'test-password-123'});self.assertEqual(r.status_code,302)
        self.assertIn('no-store',self.client.get('/patient/dashboard').headers['Cache-Control'])
    def test_invalid_schedule_no_identity_auto_link(self):
        self.login('admin');r=self.client.post('/admin/portal',data={'action':'schedule','doctor':1,'weekday':0,'start':'12:00','end':'09:00','minutes':30},follow_redirects=True);self.assertIn(b'Invalid schedule',r.data)
        self.client.post('/patient/logout');r=self.client.post('/patient/register',data={'name':'Fake','email':'alice@test.com','password':'test-password-123'},follow_redirects=True)
        self.assertIn(b'already registered',r.data)


    def test_user_admin_creates_linked_doctor_and_blocks_duplicate(self):
        self.login('admin')
        data={'full_name':'Dr Two','email':'newdoctor@clinic.test','password':'test-password-123','role':'Doctor','doctor_id':'2'}
        self.assertEqual(self.client.post('/users/add',data=data).status_code,302)
        with self.app.app_context():
            account=Admin.query.filter_by(email=data['email']).one()
            self.assertEqual(DoctorAccount.query.filter_by(admin_id=account.id).one().doctor_id,2)
        data['email']='duplicate@clinic.test'
        self.client.post('/users/add',data=data)
        with self.app.app_context():self.assertIsNone(Admin.query.filter_by(email=data['email']).first())
        self.client.get('/logout')
        r=self.client.post('/staff/login',data={'email':'newdoctor@clinic.test','password':'test-password-123'},follow_redirects=True)
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.client.get('/doctor/appointments/1').status_code,404)

    def test_staff_role_boundaries_and_dashboard_privacy(self):
        matrix={'Receptionist':('/appointments','/billing','/lab-requests','/prescriptions'), 'Pharmacist':('/medicines','/patients','/laboratory','/prescriptions/add'), 'Lab Staff':('/lab-requests','/patients','/prescriptions','/users'), 'Cashier':('/billing','/patients','/prescriptions','/users')}
        for role,paths in matrix.items():
            with self.app.app_context():
                a=Admin(full_name=role,email=role.replace(' ','').lower()+'@test.com',password=generate_password_hash('test-password-123'),role=role);db.session.add(a);db.session.commit()
            self.client.get('/logout')
            r=self.client.post('/staff/login',data={'email':role.replace(' ','').lower()+'@test.com','password':'test-password-123'},follow_redirects=True)
            self.assertEqual(r.status_code,200,role)
            self.assertNotIn(b'PRIVATE-BOB',r.data)
            self.assertEqual(self.client.get(paths[0]).status_code,200,(role,paths[0]))
            for path in paths[1:]:self.assertEqual(self.client.get(path).status_code,403,(role,path))

    def test_admin_needs_explicit_clinical_permission(self):
        self.app.config['CLINICAL_ADMIN_IDS']=''
        self.login('admin')
        for path in ['/doctor/dashboard','/doctor/appointments/1','/prescriptions','/lab-requests','/admin/reports/1/publish']:
            self.assertEqual(self.client.get(path).status_code,403,path)
        self.assertEqual(self.client.get('/users').status_code,200)

    def test_doctor_test_request_is_bound_to_assigned_appointment(self):
        self.login('doctor')
        self.assertEqual(self.client.post('/doctor/appointments/2/request-test',data={'laboratory_id':1}).status_code,404)
        self.assertEqual(self.client.post('/doctor/appointments/1/request-test',data={'laboratory_id':1}).status_code,302)
        with self.app.app_context():
            lab=LabRequest.query.order_by(LabRequest.id.desc()).first()
            self.assertEqual((lab.patient_id,lab.doctor_id,lab.status),(1,1,'Pending'))

    def test_doctor_owns_schedule_admin_can_manage_all(self):
        self.login('doctor')
        self.assertEqual(self.client.get('/staff/availability').status_code,200)
        self.assertEqual(self.client.post('/staff/availability',data={'doctor':2,'action':'remove_day','weekday':0}).status_code,403)
        r=self.client.post('/staff/availability',data={'doctor':1,'action':'schedule','weekdays':['0','1'],'start':'10:00','end':'12:00','minutes':30},follow_redirects=True)
        self.assertEqual(r.status_code,200)
        with self.app.app_context():self.assertEqual(DoctorSchedule.query.filter_by(doctor_id=1,weekday=0).one().start_time,time(10))
        self.client.get('/logout');self.login('admin')
        self.assertEqual(self.client.post('/staff/availability',data={'doctor':2,'action':'schedule','weekdays':['2'],'start':'08:00','end':'10:00','minutes':30}).status_code,302)
        with self.app.app_context():self.assertEqual(DoctorSchedule.query.filter_by(doctor_id=2,weekday=2).count(),1)

    def test_leave_blocks_overlapping_slots_and_booking_without_leaking_reason(self):
        self.login('doctor')
        data={'doctor':1,'action':'unavailable','starts_at':str(self.day)+'T09:45','ends_at':str(self.day)+'T10:15','reason':'PRIVATE-EMERGENCY'}
        self.assertEqual(self.client.post('/staff/availability',data=data).status_code,302)
        self.client.get('/logout')
        page=self.client.get('/book',query_string={'doctor':1,'date':str(self.day)})
        self.assertIn(b'Not available',page.data);self.assertNotIn(b'PRIVATE-EMERGENCY',page.data)
        from app.portal import available
        with self.app.app_context():
            slots=available(1,self.day)
            self.assertNotIn('09:30',slots);self.assertNotIn('10:00',slots);self.assertIn('10:30',slots)
        self.login()
        self.client.post('/book',data={'doctor':1,'date':str(self.day),'time':'09:30'})
        with self.app.app_context():self.assertEqual(Appointment.query.count(),2)

    def test_leave_existing_booking_warning_and_remove_restores_slots(self):
        self.login('doctor')
        self.client.post('/staff/availability',data={'doctor':1,'action':'unavailable','starts_at':str(self.day)+'T00:00','ends_at':str(self.day+timedelta(days=1))+'T00:00','reason':'Leave'})
        page=self.client.get('/staff/availability');self.assertIn(b'contact patient',page.data)
        with self.app.app_context():
            self.assertEqual(db.session.get(Appointment,1).status,'Confirmed');period=DoctorUnavailability.query.one().id
        self.client.get('/logout');self.login()
        self.assertIn(b'Your doctor is unavailable',self.client.get('/patient/dashboard').data)
        self.assertEqual(self.client.post('/patient/appointments/1/reschedule',data={'date':str(self.day),'time':'10:30'}).status_code,409)
        self.client.post('/patient/logout');self.login('doctor')
        self.client.post('/staff/availability',data={'doctor':1,'action':'remove_unavailable','period':period})
        from app.portal import available
        with self.app.app_context():self.assertIn('10:30',available(1,self.day))

    def test_unavailability_permissions_invalid_range_and_remove_day(self):
        self.login()
        self.assertEqual(self.client.get('/staff/availability').status_code,403)
        self.client.post('/patient/logout');self.login('doctor')
        self.client.post('/staff/availability',data={'doctor':1,'action':'unavailable','starts_at':str(self.day)+'T12:00','ends_at':str(self.day)+'T09:00'})
        with self.app.app_context():self.assertEqual(DoctorUnavailability.query.count(),0)
        self.client.post('/staff/availability',data={'doctor':1,'action':'remove_day','weekday':self.day.weekday()})
        page=self.client.get('/book',query_string={'doctor':1,'date':str(self.day)})
        self.assertIn(b'has not published working hours',page.data)

    def test_changed_grid_does_not_offer_overlapping_existing_booking(self):
        self.login('doctor')
        self.client.post('/staff/availability',data={'doctor':1,'action':'schedule','weekdays':[str(self.day.weekday())],'start':'09:15','end':'12:00','minutes':15})
        from app.portal import available
        with self.app.app_context():
            slots=available(1,self.day);self.assertNotIn('09:15',slots);self.assertIn('09:30',slots)

    def test_doctor_cannot_remove_another_doctors_leave(self):
        with self.app.app_context():
            p=DoctorUnavailability(doctor_id=2,starts_at=datetime.combine(self.day,time(9)),ends_at=datetime.combine(self.day,time(11)),reason='Private leave')
            db.session.add(p);db.session.commit();pid=p.id
        self.login('doctor')
        self.assertEqual(self.client.post('/staff/availability',data={'doctor':1,'action':'remove_unavailable','period':pid}).status_code,403)
        with self.app.app_context():self.assertIsNotNone(db.session.get(DoctorUnavailability,pid))
