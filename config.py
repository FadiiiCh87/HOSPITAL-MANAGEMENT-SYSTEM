import os

# Project Root Directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    database_url = os.getenv(
        "DATABASE_URL",
        "mysql+mysqlconnector://root:@localhost/hospital_management",
    )
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    SQLALCHEMY_DATABASE_URI = database_url

    # Disable Modification Tracking
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    if database_url.startswith(("postgresql://", "postgresql+")) and os.getenv("DB_SCHEMA"):
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
            "options": f"-csearch_path={os.getenv('DB_SCHEMA')}"
        }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

    # Upload Folder for Doctor Images
    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "app",
        "static",
        "uploads",
        "doctors"
    )

    # Maximum Upload Size (5 MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
