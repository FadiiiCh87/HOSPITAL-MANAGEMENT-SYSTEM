import os
import re

from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.department import Department
from werkzeug.security import generate_password_hash
from sqlalchemy import text

app = create_app()

with app.app_context():
    schema = os.getenv("DB_SCHEMA")
    if schema:
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema):
            raise RuntimeError("DB_SCHEMA contains unsupported characters")
        if os.getenv("CREATE_DB_SCHEMA", "false").lower() in {"1", "true", "yes"}:
            db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
            db.session.commit()

    db.create_all()
    from sqlalchemy import inspect
    if 'duration_minutes' not in {c['name'] for c in inspect(db.engine).get_columns('appointments')}:
        db.session.execute(text('ALTER TABLE appointments ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 30'))
        db.session.commit()
    # Additive V2 migration, run as the application schema owner.
    from app.models.appointment import Appointment
    for index in Appointment.__table__.indexes:
        if index.name == "uq_active_doctor_slot":
            saved = next((item for item in inspect(db.engine).get_indexes('appointments') if item['name'] == index.name), None)
            # Rejected requests release the slot. Replace the old predicate atomically.
            with db.engine.begin() as connection:
                if saved and 'Rejected' not in str(saved.get('dialect_options', {})):
                    index.drop(bind=connection, checkfirst=True)
                index.create(bind=connection, checkfirst=True)

    admin_email = os.getenv("ADMIN_EMAIL", "admin@hospital.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD must be set before database initialization")

    # Create Default Admin
    if not Admin.query.filter_by(email=admin_email).first():

        admin = Admin(
            full_name="System Administrator",
            email=admin_email,
            password=generate_password_hash(admin_password),
            role="Admin",
        )

        db.session.add(admin)

    # Default Departments
    departments = [
        "Cardiology",
        "Neurology",
        "Orthopedics",
        "ENT",
        "Emergency",
        "Radiology",
        "Laboratory",
        "Pharmacy"
    ]

    for dept in departments:

        if not Department.query.filter_by(name=dept).first():

            db.session.add(
                Department(name=dept)
            )

    db.session.commit()

    # Populate the initial diagnostic catalog once; never overwrite staff prices.
    from app.models.laboratory import Laboratory
    if not Laboratory.query.first():
        diagnostic_catalog = {
                "Blood Test": [
                        "Complete Blood Count (CBC)",
                        "CBC with Differential",
                        "Hemoglobin",
                        "Platelet Count",
                        "Peripheral Blood Smear",
                        "Reticulocyte Count",
                        "ESR",
                        "C-Reactive Protein (CRP)",
                        "High-Sensitivity CRP",
                        "Blood Group and Rh Type",
                        "Antibody Screen",
                        "Direct Coombs Test",
                        "Indirect Coombs Test",
                        "PT / INR",
                        "APTT",
                        "Fibrinogen",
                        "D-Dimer",
                        "Fasting Blood Glucose",
                        "Random Blood Glucose",
                        "HbA1c",
                        "Oral Glucose Tolerance Test",
                        "Basic Metabolic Panel (BMP)",
                        "Comprehensive Metabolic Panel (CMP)",
                        "Renal Function Panel",
                        "Urea",
                        "Creatinine",
                        "eGFR",
                        "Sodium",
                        "Potassium",
                        "Chloride",
                        "Bicarbonate",
                        "Calcium",
                        "Magnesium",
                        "Phosphate",
                        "Liver Function Panel",
                        "ALT",
                        "AST",
                        "Alkaline Phosphatase (ALP)",
                        "GGT",
                        "Total Bilirubin",
                        "Direct Bilirubin",
                        "Albumin",
                        "Total Protein",
                        "Lipid Profile",
                        "Total Cholesterol",
                        "HDL Cholesterol",
                        "LDL Cholesterol",
                        "Triglycerides",
                        "Uric Acid",
                        "Amylase",
                        "Lipase",
                        "Troponin",
                        "Creatine Kinase (CK)",
                        "BNP",
                        "NT-proBNP",
                        "TSH",
                        "Free T4",
                        "Free T3",
                        "Thyroid Peroxidase Antibodies",
                        "Thyroglobulin Antibodies",
                        "Ferritin",
                        "Serum Iron",
                        "Total Iron Binding Capacity (TIBC)",
                        "Transferrin Saturation",
                        "Vitamin B12",
                        "Folate",
                        "Vitamin D (25-OH)",
                        "Parathyroid Hormone (PTH)",
                        "Cortisol",
                        "Prolactin",
                        "FSH",
                        "LH",
                        "Estradiol",
                        "Progesterone",
                        "Testosterone",
                        "Beta-hCG (Quantitative)",
                        "PSA (Total)",
                        "PSA (Free)",
                        "Rheumatoid Factor",
                        "Anti-CCP Antibodies",
                        "ANA",
                        "Anti-dsDNA Antibodies",
                        "Complement C3",
                        "Complement C4",
                        "IgG",
                        "IgA",
                        "IgM",
                        "Total IgE",
                        "Tissue Transglutaminase IgA",
                        "Hepatitis B Surface Antigen",
                        "Hepatitis B Surface Antibody",
                        "Hepatitis C Antibody",
                        "HIV Antigen / Antibody",
                        "Syphilis Screening",
                        "Blood Culture",
                        "Malaria Blood Film",
                        "Dengue NS1 Antigen",
                        "Dengue IgM / IgG",
                        "Hepatitis A IgM"
                ],
                "Urine Test": [
                        "Urinalysis",
                        "Urine Microscopy",
                        "Urine Culture and Sensitivity",
                        "Urine Pregnancy Test",
                        "Urine Albumin / Creatinine Ratio",
                        "Urine Protein / Creatinine Ratio",
                        "24-Hour Urine Protein",
                        "24-Hour Urine Creatinine"
                ],
                "X-Ray": [
                        "Chest X-Ray",
                        "Abdominal X-Ray",
                        "Pelvis X-Ray",
                        "Cervical Spine X-Ray",
                        "Thoracic Spine X-Ray",
                        "Lumbar Spine X-Ray",
                        "Shoulder X-Ray",
                        "Elbow X-Ray",
                        "Wrist X-Ray",
                        "Hand X-Ray",
                        "Hip X-Ray",
                        "Knee X-Ray",
                        "Ankle X-Ray",
                        "Foot X-Ray",
                        "Femur X-Ray",
                        "Tibia / Fibula X-Ray",
                        "Humerus X-Ray",
                        "Forearm X-Ray",
                        "Rib X-Ray",
                        "Dental Panoramic X-Ray",
                        "Mammography"
                ],
                "Ultrasound": [
                        "Abdominal Ultrasound",
                        "Pelvic Ultrasound",
                        "Kidney / Bladder Ultrasound",
                        "Thyroid Ultrasound",
                        "Breast Ultrasound",
                        "Scrotal Ultrasound",
                        "Soft Tissue Ultrasound",
                        "Obstetric Ultrasound",
                        "Obstetric Anatomy Ultrasound",
                        "Transvaginal Ultrasound",
                        "Carotid Doppler Ultrasound",
                        "Lower Limb Venous Doppler",
                        "Lower Limb Arterial Doppler",
                        "Upper Limb Venous Doppler",
                        "Renal Artery Doppler"
                ],
                "MRI": [
                        "MRI Brain",
                        "MRI Pituitary",
                        "MRI Orbits",
                        "MRI Cervical Spine",
                        "MRI Thoracic Spine",
                        "MRI Lumbar Spine",
                        "MRI Shoulder",
                        "MRI Elbow",
                        "MRI Wrist",
                        "MRI Hip",
                        "MRI Knee",
                        "MRI Ankle",
                        "MRI Abdomen",
                        "MRI Pelvis",
                        "MRI Breast",
                        "Cardiac MRI",
                        "MRCP",
                        "MR Angiography",
                        "MR Venography"
                ],
                "CT Scan": [
                        "CT Head",
                        "CT Sinuses",
                        "CT Neck",
                        "CT Chest",
                        "CT Abdomen",
                        "CT Pelvis",
                        "CT Abdomen and Pelvis",
                        "CT KUB (Non-contrast)",
                        "CT Cervical Spine",
                        "CT Thoracic Spine",
                        "CT Lumbar Spine",
                        "CT Pulmonary Angiography",
                        "CT Coronary Angiography",
                        "CT Aortic Angiography",
                        "High-Resolution CT Chest",
                        "Low-Dose CT Chest"
                ],
                "ECG": [
                        "Resting ECG (12-Lead)",
                        "Exercise ECG / Treadmill Test",
                        "24-Hour Holter Monitoring",
                        "48-Hour Holter Monitoring"
                ],
                "Other": [
                        "Echocardiogram",
                        "Stress Echocardiogram",
                        "Spirometry",
                        "Pulmonary Function Tests",
                        "Peak Expiratory Flow",
                        "EEG",
                        "Nerve Conduction Studies",
                        "Electromyography (EMG)",
                        "Sleep Study (Polysomnography)",
                        "Audiometry",
                        "Tympanometry",
                        "Visual Field Test",
                        "Optical Coherence Tomography (OCT)",
                        "Bone Density Scan (DEXA)",
                        "PET-CT",
                        "Bone Scintigraphy",
                        "Thyroid Scintigraphy",
                        "Renal Scintigraphy",
                        "Stool Routine / Microscopy",
                        "Stool Culture",
                        "Stool Occult Blood (FIT)",
                        "Stool Ova and Parasites",
                        "Stool H. pylori Antigen",
                        "H. pylori Urea Breath Test",
                        "Fecal Calprotectin",
                        "Sputum Culture",
                        "Sputum AFB Smear",
                        "Tuberculosis PCR",
                        "Interferon Gamma Release Assay (TB)",
                        "Throat Swab Culture",
                        "Wound Swab Culture",
                        "COVID-19 PCR",
                        "Influenza A / B PCR",
                        "RSV PCR",
                        "Cervical Cytology (Pap Smear)",
                        "HPV Test",
                        "Histopathology (Biopsy)",
                        "Fine Needle Aspiration Cytology",
                        "Semen Analysis",
                        "Cerebrospinal Fluid Analysis",
                        "Synovial Fluid Analysis"
                ]
        }
        description = (
            "Catalog entry only. Price 0 is a placeholder: rate pending, not free. "
            "Confirm hospital availability and actual price before ordering or billing. "
            "Protocol, contrast, laterality, specimen and preparation must be specified "
            "by authorized clinical staff when applicable."
        )
        for category, names in diagnostic_catalog.items():
            for name in names:
                db.session.add(Laboratory(
                    test_name=name, category=category, price=0,
                    description=description,
                ))
        db.session.commit()
        print("Imported 223 diagnostic catalog entries; prices pending.")
    else:
        print("Existing diagnostic catalog preserved; no prices changed.")

    print("Database Seeded Successfully!")
