from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, echo=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


"""docker compose up -d
docker compose ps
docker compose exec db psql -U receptionist -c "create database receptionist_test"""
class Base(DeclarativeBase):
    pass


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
