import logging

from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import Config

# Configuration instance
config = Config()

# SQLAlchemy setup
engine = create_engine(config.DATABASE_URL)  # Create SQLAlchemy engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Session factory
Base = declarative_base()  # Base for declarative models
logger = logging.getLogger(__name__)  # Get root logger


def configure_logging(app):
    """Configures logging for the FastAPI application."""
    logging.basicConfig(level=config.LOG_LEVEL,
                        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s')
    logger.setLevel(config.LOG_LEVEL)  # Set root logger level
    app.logger = logger  # Attach logger to FastAPI app instance (optional, if you want to use app.logger)
    return logger  # Return the logger instance


def get_engine():
    yield engine


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db  # The session will be provided to route handlers as needed
    finally:
        db.close()  # Ensure the session is closed after the request


# Function to initialize extensions (database setup, etc.)
def init_extensions(app: FastAPI, schema: str = 'public'):
    """
    Initializes the extensions required by the app (e.g., database tables).
    This function is typically used for setting up initial configurations.
    """
    # Set the search path to the specified schema (e.g., 'sales', 'public', etc.)
    with engine.connect() as connection:
        connection.execute(text(f"SET search_path TO {schema};"))

    # Create tables in the database if they don't exist
    Base.metadata.create_all(bind=engine)

    # Further initialization for other extensions (e.g., rate limiting) can be added here.
    logger.info(f"Database tables initialized with schema: {schema}")
