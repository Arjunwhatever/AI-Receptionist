from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app import booking
from app.models import Tenant, Service

SlOT_STEP = timedelta(minutes=30)

IST = ZoneInfo("Asia/Kolkata")
Day = date(2026,11,2)

def at(hour, minute=0):
    return datetime(Day.year, Day.month, Day.day, hour, minute, tzinfo=IST)

def test_empty_day_returns_all_slots(db):
    slots = booking.get_available_slots(db, Tenant.id, Service.id, Day)
    assert slots[0] == at(9)
    assert slots[-1] == at(16)
    assert len(slots) == 15


class BookingError(Exception):
    pass
class NotFound(BookingError):
    pass
class OutsideHours(BookingError):
    pass
class SlotUnavailable(BookingError):
    pass


def _get_tenant_service(db: Session, tenant_id: int, service_id:int):
    tenant = db.get(Tenant, tenant_id)
    service = db.get(Service , service_id)
    if tenant is None or service is None or service.tenant_id != tenant.id:
        raise NotFound("Tenant or service not found")
    return tenant, service

def _day_bounds(tenant: Tenant, day: date):
    tz = ZoneInfo(tenant.timezone)
    opens = datetime.combine(day, tenant.open_time, tzinfo=tz)
    closes = datetime.combine(day, tenant.close_time, tzinfo=tz)
    return opens, closes

def get_available_slots(db: Session, tenant_id: int, service_id: int, day: date):
    tenant, service = _get_tenant_service(db, tenant_id, service_id)
    duration = timedelta(minutes=service.duration_minutes)
    opens, closes = _day_bounds(tenant, day)

    slots = []
    start = opens
    while start + duration <= closes:
        slots.append(start.astimezone(timezone.utc))
        start += SlOT_STEP
    return slots

PHONE = "+911234567890"


def test_booked_appointment_removes_overlapping_slots(db, tenant, service):
    booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    slots = booking.get_available_slots(db, tenant.id, service.id, Day)

    assert at(9) in slots           # 9:00-10:00 ends exactly when 10:00 starts
    assert at(9, 30) not in slots   # 9:30-10:30 overlaps
    assert at(10) not in slots      # same time
    assert at(10, 30) not in slots  # 10:30-11:30 overlaps
    assert at(11) in slots          # starts exactly when the booking ends
    assert len(slots) == 12         # 15 minus the 3 blocked