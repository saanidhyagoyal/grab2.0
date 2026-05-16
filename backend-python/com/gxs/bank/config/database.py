from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from com.gxs.bank.config.runtime import settings


connect_args: dict[str, object] = {}
extra_engine_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
if settings.database_url == "sqlite:///:memory:":
    extra_engine_args["poolclass"] = StaticPool

engine = create_engine(
    settings.database_url,
    echo=settings.show_sql,
    future=True,
    connect_args=connect_args,
    **extra_engine_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
