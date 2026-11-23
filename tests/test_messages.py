import pytest

from app import booking, messages

PHONE = "+911234567890"


def test_leave_message_saves(db, tenant):
    msg = messages.leave_message(db, tenant.id, "Asha", PHONE, "Please call me about my order")
    assert msg.id is not None
    assert msg.status == "new"
    assert msg.caller_phone == PHONE


def test_empty_message_rejected(db, tenant):
    with pytest.raises(booking.InvalidDetails):
        messages.leave_message(db, tenant.id, "Asha", PHONE, "   ")


def test_empty_name_rejected(db, tenant):
    with pytest.raises(booking.InvalidDetails):
        messages.leave_message(db, tenant.id, "", PHONE, "Hello")


def test_bad_phone_rejected(db, tenant):
    with pytest.raises(booking.InvalidDetails):
        messages.leave_message(db, tenant.id, "Asha", "123", "Hello")


def test_unknown_business_rejected(db):
    with pytest.raises(booking.NotFound):
        messages.leave_message(db, 999999, "Asha", PHONE, "Hello")

def leave_message(db, tenant_id, caller_name, body):
    db.get(Tenant, tenant_id)
    with pytest.raises(booking.NotFound):
        messages.leave_message(db, tenant_id, caller_name, PHONE, body)
        
