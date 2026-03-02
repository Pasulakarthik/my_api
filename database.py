from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_url = "postgresql+psycopg2://fastapi_user:karthik8267@localhost:5432/fastapi_db"


engine = create_engine(db_url)

SessionLocal = sessionmaker(engine , autocommit = False, autoflush=False,)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()