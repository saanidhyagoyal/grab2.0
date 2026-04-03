import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_expiration_ms: int
    cors_allowed_origins: list[str]
    show_sql: bool


def _as_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    raw_origins = os.getenv("APP_CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///:memory:"),
        jwt_secret=os.getenv(
            "APP_JWT_SECRET",
            "GxsBankSuperSecretKeyForJWT2026ThatIsLongEnoughForHS512Algorithm!!",
        ),
        jwt_expiration_ms=int(os.getenv("APP_JWT_EXPIRATION_MS", "86400000")),
        cors_allowed_origins=[item.strip() for item in raw_origins.split(",") if item.strip()],
        show_sql=_as_bool(os.getenv("SQL_SHOW"), False),
    )


settings = load_settings()
