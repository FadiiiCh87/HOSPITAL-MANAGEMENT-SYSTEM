import os

# Project Root Directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    # Secret Key
    SECRET_KEY = "hospital_secret_key"

    # MySQL Database
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:@localhost/hospital_management"

    # Disable Modification Tracking
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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