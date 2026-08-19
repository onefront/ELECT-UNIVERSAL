import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///elect_universal.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "uploads"
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # BMS SMS Gateway
    BMS_API_KEY = os.getenv("BMS_API_KEY", "")
    BMS_SENDER_ID = os.getenv("BMS_SENDER_ID", "")
    BMS_ENABLED = os.getenv(
        "BMS_ENABLED",
        "false"
    ).lower() == "true"