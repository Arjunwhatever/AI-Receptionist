import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.llm import chat
from app.agent.tools import TOOLS, execute_tool
from app.models import Service, Tenant

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


def build_system_prompt(db: Session, tenant_id: int) -> str:
    tenant = db.get(Tenant, tenant_id)
    services = db.execute(
        select(Service).where(Service.tenant_id == tenant_id)
    ).scalars().all()
    now = datetime.now(ZoneInfo(tenant.timezone))
    menu = "\n".join(
        f"- id {s.id}: {s.name}, {s.duration_minutes} min, price {s.price}"
        for s in services
    )
    return f"""You are the phone receptionist for {tenant.name}.
Today is {now:%A %Y-%m-%d} and the time is {now:%H:%M} ({tenant.timezone}).
Opening hours: {tenant.open_time:%H:%M} to {tenant.close_time:%H:%M}.

Services:
{menu}

Rules:
- Keep replies short and natural, as if speaking on the phone.
- Never guess availability. Always call get_available_slots before offering times.
- To book you need: the service, the date and time, the caller's name, and the caller's phone number. Ask for anything missing, one question at a time.
- Never invent a name or a phone number.
- Confirm the details with the caller before calling book_appointment.
- If a tool returns an error, explain it simply and offer an alternative."""


def respond(db: Session, tenant_id: int, messages: list[dict], user_text: str) -> str:
    """Add the caller's message, run the tool loop, and return the reply text.

    `messages` is the running conversation and is updated in place.
    """
    messages.append({"role": "user", "content": user_text})

    for _ in range(MAX_TOOL_ROUNDS):
        reply = chat(messages, TOOLS)
        messages.append(reply)

        tool_calls = reply.get("tool_calls")
        if not tool_calls:
            return reply["content"]

        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            result = execute_tool(db, tenant_id, name, args)
            db.commit()
            logger.info("tool %s %s -> %s", name, args, result)
            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": json.dumps(result),
            })

    return "Sorry, I'm having trouble with that. Could you say that again?"