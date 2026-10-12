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
        self.app=create_app({'TESTING':True,'SECRET_KEY':'test-secret','SQLALCHEMY_DATABASE_URI':'sqlite:///'+self.path,'SQLALCHEMY_ENGINE_OPTIONS':{},'WTF_CSRF_ENABLED':False,'SESSION_COOKIE_SECURE':False})
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

if __name__=='__main__':unittest.main()
