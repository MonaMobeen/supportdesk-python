import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/uploads")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
OVERDUE_THRESHOLD_HOURS = int(os.getenv("OVERDUE_THRESHOLD_HOURS", "48"))