from datetime import time

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Service, Tenant

with SessionLocal() as db:
    if db.execute(select(Tenant.id)).first():
        print("Already seeded.")
    else:
        tenant = Tenant(name="Glow Salon", timezone="Asia/Kolkata",
                        open_time=time(9, 0), close_time=time(17, 0))
        db.add(tenant)
        db.flush()
        db.add_all([
            Service(tenant_id=tenant.id, name="Haircut", duration_minutes=60, price=500),
            Service(tenant_id=tenant.id, name="Beard trim", duration_minutes=30, price=250),
        ])
        db.commit()
        print("Seeded tenant", tenant.id)