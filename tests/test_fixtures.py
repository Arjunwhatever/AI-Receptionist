from sqlalchemy import text

def test_fixtures_work(db, tenant, service):
    assert tenant.id is not None
    assert service.tenant_id == tenant.id
    assert db.execute(text("select current_database()")).scalar() == "receptionist_test"