from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# db_url = os.getenv("DATABASE_URL")
DATABASE_URL = "postgresql://neondb_owner:npg_D4s2TFjAOXze@ep-flat-fog-a4q85elu-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"



# engine = create_engine(db_url,pool_pre_ping=True)
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)

SessionLocal = sessionmaker(engine , autocommit = False, autoflush=False,)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


