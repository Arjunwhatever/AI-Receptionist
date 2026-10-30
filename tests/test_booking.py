from datetime import date, datetime
from zoneinfo import ZoneInfo

from app import booking

IST = ZoneInfo("Asia/Kolkata")
Day = date(2026, 11, 2)
PHONE = "+911234567890"


def at(hour, minute=0):
    return datetime(Day.year, Day.month, Day.day, hour, minute, tzinfo=IST)


def test_empty_day_returns_all_slots(db, tenant, service):
    slots = booking.get_available_slots(db, tenant.id, service.id, Day)
    assert slots[0] == at(9)
    assert slots[-1] == at(16)
    assert len(slots) == 15


def test_booked_appointment_removes_overlapping_slots(db, tenant, service):
    booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    slots = booking.get_available_slots(db, tenant.id, service.id, Day)

    assert at(9) in slots           # 9:00-10:00 ends exactly when 10:00 starts
    assert at(9, 30) not in slots   # 9:30-10:30 overlaps
    assert at(10) not in slots      # same time
    assert at(10, 30) not in slots  # 10:30-11:30 overlaps
    assert at(11) in slots          # starts exactly when the booking ends
    assert len(slots) == 12         # 15 minus the 3 blocked