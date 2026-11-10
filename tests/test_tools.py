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