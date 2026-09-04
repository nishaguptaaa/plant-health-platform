"""Database engine and session configuration."""

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "private" / "plant_health.db"
DEFAULT_DATABASE_URL = f"sqlite+pysqlite:///{DEFAULT_DATABASE_PATH}"


def _enable_sqlite_foreign_keys(
    dbapi_connection: object,
    _connection_record: object,
) -> None:
    """Enable foreign-key enforcement for each SQLite connection."""

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def create_database_engine(
    database_url: str = DEFAULT_DATABASE_URL,
    *,
    echo: bool = False,
) -> Engine:
    """Create an engine that can use SQLite now and PostgreSQL later."""

    url = make_url(database_url)

    if url.get_backend_name() == "sqlite" and url.database not in (None, ":memory:"):
        Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(database_url, echo=echo)

    if url.get_backend_name() == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create database sessions bound to the supplied engine."""

    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )