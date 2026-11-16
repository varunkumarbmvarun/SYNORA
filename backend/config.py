import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
LOGS_DIR = BACKEND_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BACKEND_DIR / "college_kb.db"))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_FILE = str(LOGS_DIR / "app.log")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1")
    CORS_ORIGINS = ["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000"]
