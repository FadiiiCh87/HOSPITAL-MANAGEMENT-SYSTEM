# Hospital Management System

Production-ready Hospital Management System developed using Flask, SQLAlchemy,
PostgreSQL/MySQL and Bootstrap.

## Version

v1.0

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
