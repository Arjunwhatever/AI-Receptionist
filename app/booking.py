from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appointment, Service, Tenant

SLOT_STEP = timedelta(minutes=30)


class BookingError(Exception):
    pass


class NotFound(BookingError):
    pass


class OutsideHours(BookingError):
    pass


class SlotUnavailable(BookingError):
    pass


def _get_tenant_service(db: Session, tenant_id: int, service_id: int):
    tenant = db.get(Tenant, tenant_id)
    service = db.get(Service, service_id)
    if tenant is None or service is None or service.tenant_id != tenant.id:
        raise NotFound("Tenant or service not found")
    return tenant, service


def _day_bounds(tenant: Tenant, day: date):
    tz = ZoneInfo(tenant.timezone)
    opens = datetime.combine(day, tenant.open_time, tzinfo=tz)
    closes = datetime.combine(day, tenant.close_time, tzinfo=tz)
    return opens, closes


def _has_conflict(db: Session, tenant_id: int, starts_at, ends_at, exclude_id=None):
    query = select(Appointment.id).where(
        Appointment.tenant_id == tenant_id,
        Appointment.status == "booked",
        Appointment.starts_at < ends_at,
        Appointment.ends_at > starts_at,
    )
    if exclude_id is not None:
        query = query.where(Appointment.id != exclude_id)
    return db.execute(query.limit(1)).first() is not None


def book(db: Session, tenant_id: int, service_id: int,
         customer_name: str, customer_phone: str, starts_at: datetime):
    tenant, service = _get_tenant_service(db, tenant_id, service_id)
    ends_at = starts_at + timedelta(minutes=service.duration_minutes)

    appointment = Appointment(
        tenant_id=tenant_id, service_id=service_id,
        customer_name=customer_name, customer_phone=customer_phone,
        starts_at=starts_at, ends_at=ends_at, status="booked",
    )
    db.add(appointment)
    db.flush()
    return appointment


def get_available_slots(db: Session, tenant_id: int, service_id: int, day: date):
    tenant, service = _get_tenant_service(db, tenant_id, service_id)
    duration = timedelta(minutes=service.duration_minutes)
    opens, closes = _day_bounds(tenant, day)

    slots = []
    start = opens
    while start + duration <= closes:
        if not _has_conflict(db, tenant_id, start, start + duration):
            slots.append(start.astimezone(timezone.utc))
        start += SLOT_STEP
    return slots