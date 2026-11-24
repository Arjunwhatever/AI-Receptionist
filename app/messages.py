from sqlalchemy.orm import Session

from app import booking
from app.models import OwnerMessage, Tenant

MAX_BODY_LENGTH = 1000


def leave_message(db: Session, tenant_id: int, caller_name: str,
                  caller_phone: str, body: str) -> OwnerMessage:
    if db.get(Tenant, tenant_id) is None:
        raise booking.NotFound("Business not found")

    name = caller_name.strip()
    text = body.strip()
    if not name:
        raise booking.InvalidDetails("A name is needed")
    if not text:
        raise booking.InvalidDetails("The message is empty")
    if len(text) > MAX_BODY_LENGTH:
        raise booking.InvalidDetails("The message is too long, please shorten it")
    booking.check_phone(caller_phone)

    message = OwnerMessage(
        tenant_id=tenant_id,
        caller_name=name,
        caller_phone=booking.normalize_phone(caller_phone),
        body=text,
    )
    db.add(message)
    db.flush()
    return message