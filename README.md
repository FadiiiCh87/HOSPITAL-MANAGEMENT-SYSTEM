# Hospital Management System

Production-ready Hospital Management System developed using Flask, SQLAlchemy,
PostgreSQL/MySQL and Bootstrap.

## Version

v2.0

## Modules

- Authentication
- Dashboard
- Doctors
- Departments
- Patients
- Appointments
- Pharmacy
- Medicine Categories
- Laboratory
- Lab Requests
- Prescriptions
- Billing
- Reports
- User Management

## Production deployment

Required environment variables:

- `DATABASE_URL`: PostgreSQL connection URL
- `SECRET_KEY`: long random Flask signing secret
- `ADMIN_EMAIL`: initial administrator email
- `ADMIN_PASSWORD`: initial administrator password
- `SESSION_COOKIE_SECURE=true`: enable secure cookies on HTTPS

Start command:

```bash
python seed.py && gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

The startup seed is idempotent: it creates missing tables, the initial admin, and
default departments without overwriting existing data. Health checks are exposed
at `/health`. Doctor images are stored in the database so they remain available
after stateless host restarts.


## Patient portal V2

- Guest landing page at `/`; separate staff login at `/staff/login`.
- Patient registration, own dashboard/profile, identity-verified enrollment of existing records.
- Weekly doctor schedules, immediate confirmed bookings, database-level slot uniqueness.
- Cancel/reschedule at least 2 hours before a visit (Saudi Arabia time, UTC+3); 90-day booking window.
- Date-wise medical timeline, checkups, follow-up booking and prescription PDFs.
- Lab request status, explicit report publishing/withdrawal, original or generated report PDFs.
- Doctor accounts linked by ID, assigned consultations and patient history.
- CSRF protection, role/ownership checks, private response caching, audit log, login throttling.
- Dashboard visit reminders. No email/SMS is sent unless delivery is configured.

Admin setup: add real doctors in the existing Doctors module, then open **V2 schedules & access** to set weekly hours and create doctor logins. Add lab requests/results in the existing Laboratory workflow; publish completed reports separately. No demo doctors or clinical data are seeded.

Database upgrade: the idempotent `seed.py` startup creates V2 tables and the appointment uniqueness index as the existing schema owner. `migrations/hospital_v2.sql` is the equivalent manual migration. The migration adds tables and an appointment uniqueness index. Existing tables/data remain intact. If older databases have duplicate active doctor/date/time slots, resolve them before adding the index. PostgreSQL grants/DDL run as the schema owner (`hospital_app` in production).

Email recovery: optional `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD`. Reset links expire after 30 minutes and are single-use; password recovery invalidates older patient sessions. Without SMTP, patients are directed to reception for identity-verified admin recovery.

Validation: `python -m unittest discover -s tests -v`.

Rollback: pre-V2 branch `backup/pre-v2-2026-10-12`, commit `f9679c998583f089cb335fceb386217dd73e6368`. Additive V2 tables can remain when restoring V1 code. A private backup archive includes source, database records/metadata, binary data and an isolated restore SQL script. Never commit the data backup or environment secrets.
