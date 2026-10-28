from datetime import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Service, Tenant

TEST_URL = "postgresql+psycopg://receptionist:receptionist@localhost:5432/receptionist_test"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    
@pytest.fixture
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def tenant(db):
    t = Tenant(
        name="Test Salon",
        timezone="Asia/Kolkata",
        open_time=time(9, 8),
        close_time=time(17, 0),
    )
    db.add(t)
    db.flush()
    return t


@pytest.fixture
def service(db, tenant):
    s = Service(
        tenant_id=tenant.id,
        name="Haircut",
        duration_minutes=30,
        price=20.00,
    )
    db.add(s)
    db.flush()
    return s
