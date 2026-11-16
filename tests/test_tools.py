from app.agent.tools import execute_tool

PHONE = "+911234567890"


def test_get_available_slots_returns_local_times(db, tenant, service):
    result = execute_tool(db, tenant.id, "get_available_slots",
                          {"service_id": service.id, "date": "2026-11-02"})
    assert result["available_times"][0] == "09:00"
    assert result["available_times"][-1] == "16:00"


def test_model_may_send_ids_as_strings(db, tenant, service):
    result = execute_tool(db, tenant.id, "get_available_slots",
                          {"service_id": str(service.id), "date": "2026-11-02"})
    assert "available_times" in result


def test_book_appointment_confirms_local_time(db, tenant, service):
    result = execute_tool(db, tenant.id, "book_appointment", {
        "service_id": service.id, "start_time": "2026-11-02T10:00",
        "customer_name": "Asha", "customer_phone": PHONE,
    })
    assert result["status"] == "booked"
    assert result["start"] == "2026-11-02 10:00"


def test_taken_slot_returns_error_instead_of_raising(db, tenant, service):
    args = {"service_id": service.id, "start_time": "2026-11-02T10:00",
            "customer_name": "Asha", "customer_phone": PHONE}
    execute_tool(db, tenant.id, "book_appointment", args)
    result = execute_tool(db, tenant.id, "book_appointment", args)
    assert "already booked" in result["error"]


def test_bad_arguments_return_error(db, tenant, service):
    result = execute_tool(db, tenant.id, "get_available_slots",
                          {"service_id": service.id, "date": "next tuesday"})
    assert "error" in result


def test_unknown_tool_returns_error(db, tenant):
    assert "error" in execute_tool(db, tenant.id, "delete_everything", {})

def _book(db, tenant, service, hour=10):
    return execute_tool(db, tenant.id, "book_appointment", {
        "service_id": service.id, "start_time": f"2026-11-02T{hour:02d}:00",
        "customer_name": "Asha", "customer_phone": PHONE,
    })


def test_find_my_appointments(db, tenant, service):
    booked = _book(db, tenant, service)
    result = execute_tool(db, tenant.id, "find_my_appointments", {"customer_phone": PHONE})
    first = result["appointments"][0]
    assert first["appointment_id"] == booked["appointment_id"]
    assert first["service"] == "Haircut"
    assert first["start"] == "2026-11-02 10:00"


def test_find_my_appointments_none(db, tenant, service):
    _book(db, tenant, service)
    result = execute_tool(db, tenant.id, "find_my_appointments", {"customer_phone": "+910000000000"})
    assert result["appointments"] == []


def test_cancel_appointment_tool(db, tenant, service):
    booked = _book(db, tenant, service)
    result = execute_tool(db, tenant.id, "cancel_appointment",
                          {"appointment_id": booked["appointment_id"], "customer_phone": PHONE})
    assert result["status"] == "cancelled"
    slots = execute_tool(db, tenant.id, "get_available_slots",
                         {"service_id": service.id, "date": "2026-11-02"})
    assert "10:00" in slots["available_times"]


def test_cancel_with_wrong_phone_returns_error(db, tenant, service):
    booked = _book(db, tenant, service)
    result = execute_tool(db, tenant.id, "cancel_appointment",
                          {"appointment_id": booked["appointment_id"], "customer_phone": "+910000000000"})
    assert "error" in result


def test_reschedule_tool(db, tenant, service):
    booked = _book(db, tenant, service)
    result = execute_tool(db, tenant.id, "reschedule_appointment", {
        "appointment_id": booked["appointment_id"], "customer_phone": PHONE,
        "new_start_time": "2026-11-02T14:00",
    })
    assert result["status"] == "rescheduled"
    assert result["start"] == "2026-11-02 14:00"


def test_reschedule_into_taken_slot_returns_error(db, tenant, service):
    _book(db, tenant, service, hour=10)
    second = _book(db, tenant, service, hour=14)
    result = execute_tool(db, tenant.id, "reschedule_appointment", {
        "appointment_id": second["appointment_id"], "customer_phone": PHONE,
        "new_start_time": "2026-11-02T10:30",
    })
    assert "already booked" in result["error"]