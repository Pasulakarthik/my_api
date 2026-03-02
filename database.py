from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

db_url = os.getenv("DATABASE_URL")


engine = create_engine(db_url)

SessionLocal = sessionmaker(engine , autocommit = False, autoflush=False,)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()