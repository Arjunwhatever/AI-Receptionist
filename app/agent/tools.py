from datetime import datetime, date 
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app import booking
from app.models import Tenant

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_available_slots",
            "description": "List the free appointment start times for a service on a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "integer", "description": "Id of the service, from the service list"},
                    "date": {"type": "string", "description": "Date as YYYY-MM-DD"},
                },
                "required": ["service_id", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment. Only call this after the caller has confirmed all details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "integer", "description": "Id of the service, from the service list"},
                    "start_time": {"type": "string", "description": "Local start time as YYYY-MM-DDTHH:MM, for example 2026-11-04T10:30"},
                    "customer_name": {"type": "string", "description": "The caller's name"},
                    "customer_phone": {"type": "string", "description": "The caller's phone number"},
                },
                "required": ["service_id", "start_time", "customer_name", "customer_phone"],
            },
        },
    },
]

def _tenant(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise booking.NotFound("Business not found")
    return tenant

def _get_available_slots(db: Session, tenant_id: int, args: dict) -> dict:
    tenant = _tenant(db, tenant_id)
    day = date.fromisoformat(args["date"])
    slots = booking.get_available_slots(db, tenant_id, int(args["service_id"]), day)
    tz = ZoneInfo(tenant.timezone)
    return {
        "date": day.isoformat(),
        "available_times": [s.astimezone(tz).strftime("%H:%M") for s in slots],
    }
def _book_appointment(db: Session, tenant_id: int, args: dict) -> dict:
    tenant = _tenant(db, tenant_id)
    tz = ZoneInfo(tenant.timezone)

    starts_at = datetime.fromisoformat(args["start_time"])
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=tz)

    name = str(args["customer_name"]).strip()
    phone = str(args["customer_phone"]).strip()
    if not name or not phone:
        raise ValueError("customer_name and customer_phone must not be empty")

    appointment = booking.book(db, tenant_id, int(args["service_id"]), name, phone, starts_at)
    return {
        "status": "booked",
        "appointment_id": appointment.id,
        "start": appointment.starts_at.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
        "end": appointment.ends_at.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
    }

def execute_tool(db: Session, tenant_id: int, name: str, args) -> dict:
    """Run one tool call. Always returns a dict; problems become {"error": ...}."""
    if not isinstance(args, dict):
        return {"error": "Arguments must be an object"}
    try:
        if name == "get_available_slots":
            return _get_available_slots(db, tenant_id, args)
        if name == "book_appointment":
            return _book_appointment(db, tenant_id, args)
        return {"error": f"Unknown tool: {name}"}
    except booking.BookingError as error:
        return {"error": str(error)}
    except (KeyError, ValueError, TypeError) as error:
        return {"error": f"Invalid arguments: {error!r}"}