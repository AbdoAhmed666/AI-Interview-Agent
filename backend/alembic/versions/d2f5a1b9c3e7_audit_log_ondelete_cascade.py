"""Add ON DELETE CASCADE to interview_audit_log foreign keys.

The audit log referenced ``interview_sessions`` and ``interview_questions``
with the default NO ACTION, so deleting a session or question while audit
rows still referenced it raised a ForeignKeyViolation. The audit trail is
owned by its session's lifecycle, so it should be removed with the rows it
references. This makes session/question deletion (and test teardown)
integrity-safe.

Revision ID: d2f5a1b9c3e7
Revises: c4f1d8e2a901
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d2f5a1b9c3e7"
down_revision: Union[str, Sequence[str], None] = "c4f1d8e2a901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "interview_audit_log_session_id_fkey",
        "interview_audit_log",
        type_="foreignkey",
    )
    op.drop_constraint(
        "interview_audit_log_question_id_fkey",
        "interview_audit_log",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "interview_audit_log_session_id_fkey",
        "interview_audit_log",
        "interview_sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "interview_audit_log_question_id_fkey",
        "interview_audit_log",
        "interview_questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "interview_audit_log_session_id_fkey",
        "interview_audit_log",
        type_="foreignkey",
    )
    op.drop_constraint(
        "interview_audit_log_question_id_fkey",
        "interview_audit_log",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "interview_audit_log_session_id_fkey",
        "interview_audit_log",
        "interview_sessions",
        ["session_id"],
        ["id"],
    )
    op.create_foreign_key(
        "interview_audit_log_question_id_fkey",
        "interview_audit_log",
        "interview_questions",
        ["question_id"],
        ["id"],
    )
