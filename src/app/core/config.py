from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "planner")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me-32-characters-minimum")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    PROJECT_DIR: Path = Path(__file__).resolve().parents[2]
    TEMPLATES_DIR: Path = PROJECT_DIR / "src" / "app" / "templates"
    HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", 10))
    HTTP_MAX_CONNECTIONS: int = int(os.getenv("HTTP_MAX_CONNECTIONS", 10))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    APP_NAME: str = os.getenv("APP_NAME", "studplanner")
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_TASKS: int = int(os.getenv("CACHE_TTL_TASKS", 900))
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", 900))
    CACHE_MAX_BYTES: int = int(os.getenv("CACHE_MAX_BYTES", 1048576))
    CACHE_TTL_PREVIEW: int = int(os.getenv("CACHE_TTL_PREVIEW", 300))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
    LOG_ROTATE_MB: int = int(os.getenv("LOG_ROTATE_MB", 10))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", 5))

    # Background tasks
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    AUTO_IMPORT_ENABLED: bool = os.getenv("AUTO_IMPORT_ENABLED", "false").lower() == "true"
    AUTO_IMPORT_INTERVAL_MINUTES: int = int(os.getenv("AUTO_IMPORT_INTERVAL_MINUTES", 60))
    CLEANUP_ENABLED: bool = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"
    CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", 24))
    CLEANUP_EXPIRED_DAYS: int = int(os.getenv("CLEANUP_EXPIRED_DAYS", 90))
    REMINDERS_ENABLED: bool = os.getenv("REMINDERS_ENABLED", "true").lower() == "true"
    REMINDER_CHECK_INTERVAL_MINUTES: int = int(os.getenv("REMINDER_CHECK_INTERVAL_MINUTES", 15))
    REMINDER_BEFORE_MINUTES: int = int(os.getenv("REMINDER_BEFORE_MINUTES", 30))

    # DI
    MONGO_POOL_SIZE: int = int(os.getenv("MONGO_POOL_SIZE", 10))
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", 10))

    @property
    def access_token_timedelta(self) -> timedelta:
        return timedelta(minutes=self.JWT_EXPIRE_MINUTES)


settings = Settings()
