from datetime import date, datetime
from zoneinfo import ZoneInfo
import pytest 
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

def test_book_overlapping_raises(db, tenant, service):
    booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    with pytest.raises(booking.SlotUnavailable):
        booking.book(db, tenant.id, service.id, "Ben", PHONE, at(10, 30))#over"larps")                     

def test_back_to_back_allowed(db , tenant, service):
    booking.book(db, tenant.id, service.id, "Asga", PHONE, at(10))
    appt = booking.book(db, tenant.id, service.id, "Ben", PHONE, at(11))
    assert appt.id is not None

def test_book_before_opening_raises(db, tenant, service):
    with pytest.raises(booking.OutsideHours):
        booking.book(db, tenant.id, service.id, "Asha", PHONE, at(8))


def test_book_past_closing_raises(db, tenant, service):
    # 16:30 + 60 minutes ends at 17:30, after the 17:00 close
    with pytest.raises(booking.OutsideHours):
        booking.book(db, tenant.id, service.id, "Asha", PHONE, at(16, 30))


def test_book_last_slot_allowed(db, tenant, service):
    # 16:00 + 60 minutes ends exactly at 17:00, which is fine
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(16))
    assert appt.id is not None

def test_cancel_marks_appointment_cancelled(db, tenant, service):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    cancelled = booking.cancel(db, tenant.id, appt.id)
    assert cancelled.status == "cancelled"


def test_cancelled_slot_is_available_again(db, tenant, service):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    booking.cancel(db, tenant.id, appt.id)
    slots = booking.get_available_slots(db, tenant.id, service.id, Day)
    assert at(10) in slots
    assert len(slots) == 15


def test_cancel_other_tenants_appointment_raises(db, tenant, service, other_tenant):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    with pytest.raises(booking.NotFound):
        booking.cancel(db, other_tenant.id, appt.id)


def test_cancel_twice_raises(db, tenant, service):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    booking.cancel(db, tenant.id, appt.id)
    with pytest.raises(booking.NotFound):
        booking.cancel(db, tenant.id, appt.id)

def test_reschedule_moves_appointment(db, tenant, service):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    moved = booking.reschedule(db, tenant.id, appt.id, at(14))
    assert moved.id == appt.id
    assert moved.starts_at == at(14)
    assert moved.ends_at == at(15)


def test_reschedule_frees_old_slot(db, tenant, service):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    booking.reschedule(db, tenant.id, appt.id, at(14))
    slots = booking.get_available_slots(db, tenant.id, service.id, Day)
    assert at(10) in slots
    assert at(14) not in slots


def test_reschedule_into_taken_slot_raises(db, tenant, service):
    booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    appt = booking.book(db, tenant.id, service.id, "Ben", PHONE, at(14))
    with pytest.raises(booking.SlotUnavailable):
        booking.reschedule(db, tenant.id, appt.id, at(10, 30))


def test_reschedule_within_own_slot(db, tenant, service):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    moved = booking.reschedule(db, tenant.id, appt.id, at(10, 30))
    assert moved.starts_at == at(10, 30)


def test_reschedule_outside_hours_raises(db, tenant, service):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    with pytest.raises(booking.OutsideHours):
        booking.reschedule(db, tenant.id, appt.id, at(16, 30))


def test_reschedule_other_tenants_appointment_raises(db, tenant, service, other_tenant):
    appt = booking.book(db, tenant.id, service.id, "Asha", PHONE, at(10))
    with pytest.raises(booking.NotFound):
        booking.reschedule(db, other_tenant.id, appt.id, at(14))