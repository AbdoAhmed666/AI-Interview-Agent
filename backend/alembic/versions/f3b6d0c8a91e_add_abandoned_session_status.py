"""Allow the ABANDONED interview session status.

Starting a new interview while another was still open left the old row as
IN_PROGRESS forever: it was never resumable in practice, it competed with the
real session for ``resume_interview``, and it dragged the dashboard's
completion rate down permanently. Sessions the candidate walked away from now
get their own terminal status, which the session CHECK constraint has to
accept.

Revision ID: f3b6d0c8a91e
Revises: d2f5a1b9c3e7
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f3b6d0c8a91e"
down_revision: Union[str, Sequence[str], None] = "d2f5a1b9c3e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_WITHOUT_ABANDONED = (
    "status IN ('IN_PROGRESS', 'GENERATING', 'GENERATION_FAILED', "
    "'READY_TO_FINISH', 'COMPLETED')"
)
_WITH_ABANDONED = (
    "status IN ('IN_PROGRESS', 'GENERATING', 'GENERATION_FAILED', "
    "'READY_TO_FINISH', 'COMPLETED', 'ABANDONED')"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_interview_sessions_status", "interview_sessions", type_="check"
    )
    op.create_check_constraint(
        "ck_interview_sessions_status", "interview_sessions", _WITH_ABANDONED
    )


def downgrade() -> None:
    # The old constraint has no room for ABANDONED, so fold those rows back
    # into the state they were abandoned from before restoring it.
    op.execute(
        "UPDATE interview_sessions SET status = 'IN_PROGRESS' "
        "WHERE status = 'ABANDONED'"
    )
    op.drop_constraint(
        "ck_interview_sessions_status", "interview_sessions", type_="check"
    )
    op.create_check_constraint(
        "ck_interview_sessions_status", "interview_sessions", _WITHOUT_ABANDONED
    )
