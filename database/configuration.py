#!/usr/bin/python3

from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Defaults to a local SQLite database sqlite:///./database/dogeapi.sqlite
# To use a different database, set the DATABASE_URL environment variable
# Example: DATABASE_URL=postgresql+psycopg2://localhost@dogeapi
SQLALCHEMY_DATABASE_URL = config(
    "DATABASE_URL", default="postgresql+psycopg2://localhost@dogeapi"
)

if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """
    Get the database session

    Yields:
        Session: The database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
