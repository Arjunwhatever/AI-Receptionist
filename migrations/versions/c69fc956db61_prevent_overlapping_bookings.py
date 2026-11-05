"""prevent overlapping bookings

Revision ID: c69fc956db61
Revises: e2b571a97202
Create Date: 2026-11-02 23:34:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c69fc956db61'
down_revision: Union[str, Sequence[str], None] = 'e2b571a97202'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("""
        ALTER TABLE appointments
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            tenant_id WITH =,
            tstzrange(starts_at, ends_at) WITH &&
        ) WHERE (status = 'booked')
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS no_overlapping_bookings")
