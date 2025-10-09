"""Database connection and session management."""

from sqlmodel import Session, SQLModel, create_engine, text

from .config import db_settings

# Create database engine
engine = create_engine(
    db_settings.connection_url,
    pool_size=db_settings.db_pool_size,
    pool_timeout=db_settings.db_pool_timeout,
    pool_recycle=db_settings.db_pool_recycle,
    echo=db_settings.debug,  # Log SQL in debug mode
)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session


def get_session_sync():
    """Get synchronous database session."""
    return Session(engine)


def test_connection():
    """Test database connection."""
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))  # type: ignore[arg-type]
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
