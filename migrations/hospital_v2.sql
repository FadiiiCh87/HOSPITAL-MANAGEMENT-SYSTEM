SET search_path TO hospital_management;

CREATE TABLE IF NOT EXISTS audit_events (
	id SERIAL NOT NULL, 
	actor VARCHAR(60) NOT NULL, 
	action VARCHAR(100) NOT NULL, 
	target VARCHAR(100) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE IF NOT EXISTS login_attempts (
	id SERIAL NOT NULL, 
	key VARCHAR(64) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE INDEX IF NOT EXISTS ix_login_attempts_key ON login_attempts (key);

CREATE TABLE IF NOT EXISTS patient_accounts (
	id SERIAL NOT NULL, 
	patient_id INTEGER NOT NULL, 
	email VARCHAR(100) NOT NULL, 
	password VARCHAR(255) NOT NULL, 
	token_version INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (patient_id), 
	FOREIGN KEY(patient_id) REFERENCES patients (id), 
	UNIQUE (email)
)

;

CREATE TABLE IF NOT EXISTS doctor_accounts (
	id SERIAL NOT NULL, 
	admin_id INTEGER NOT NULL, 
	doctor_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (admin_id), 
	FOREIGN KEY(admin_id) REFERENCES admins (id), 
	UNIQUE (doctor_id), 
	FOREIGN KEY(doctor_id) REFERENCES doctors (id)
)

;

CREATE TABLE IF NOT EXISTS doctor_schedules (
	id SERIAL NOT NULL, 
	doctor_id INTEGER NOT NULL, 
	weekday INTEGER NOT NULL, 
	start_time TIME WITHOUT TIME ZONE NOT NULL, 
	end_time TIME WITHOUT TIME ZONE NOT NULL, 
	slot_minutes INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (doctor_id, weekday), 
	FOREIGN KEY(doctor_id) REFERENCES doctors (id)
)

;

CREATE TABLE IF NOT EXISTS checkups (
	id SERIAL NOT NULL, 
	appointment_id INTEGER NOT NULL, 
	prescription_id INTEGER, 
	diagnosis TEXT NOT NULL, 
	notes TEXT, 
	follow_up DATE, 
	PRIMARY KEY (id), 
	UNIQUE (appointment_id), 
	FOREIGN KEY(appointment_id) REFERENCES appointments (id), 
	FOREIGN KEY(prescription_id) REFERENCES prescriptions (id)
)

;

CREATE TABLE IF NOT EXISTS published_reports (
	id SERIAL NOT NULL, 
	lab_request_id INTEGER NOT NULL, 
	published_at TIMESTAMP WITHOUT TIME ZONE, 
	file_data BYTEA, 
	PRIMARY KEY (id), 
	UNIQUE (lab_request_id), 
	FOREIGN KEY(lab_request_id) REFERENCES lab_requests (id)
)

;
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_doctor_slot ON appointments (doctor_id, appointment_date, appointment_time) WHERE status != 'Cancelled';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA hospital_management TO hospital_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA hospital_management TO hospital_app;
REVOKE ALL ON ALL TABLES IN SCHEMA hospital_management FROM anon, authenticated;