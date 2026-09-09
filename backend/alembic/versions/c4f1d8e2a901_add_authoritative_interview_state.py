"""Add PostgreSQL-authoritative interview state.

Revision ID: c4f1d8e2a901
Revises: b7676570a474
"""
from typing import Sequence, Union

from alembic import context
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c4f1d8e2a901"
down_revision: Union[str, Sequence[str], None] = "b7676570a474"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SESSION_STATUSES = (
    "IN_PROGRESS",
    "GENERATING",
    "GENERATION_FAILED",
    "READY_TO_FINISH",
    "COMPLETED",
)
QUESTION_STATUSES = (
    "ACTIVE",
    "EVALUATING",
    "EVALUATION_FAILED",
    "EVALUATED",
    "LEGACY_EVALUATED",
    "LEGACY_ARCHIVED",
)


def _fail(message: str) -> None:
    raise RuntimeError(f"Interview state migration precondition failed: {message}")


def _validate_source_state(connection: sa.Connection) -> None:
    statuses = {
        row[0]
        for row in connection.execute(
            sa.text("SELECT DISTINCT status FROM interview_sessions")
        )
    }
    unexpected_statuses = statuses.difference({"in_progress", "completed"})
    if unexpected_statuses:
        _fail(f"unexpected session statuses: {sorted(unexpected_statuses)}")

    over_limit = list(
        connection.execute(
            sa.text(
                """
                SELECT session_id, COUNT(*) AS question_count
                FROM interview_questions
                GROUP BY session_id
                HAVING COUNT(*) > 5
                ORDER BY session_id
                """
            )
        )
    )
    unexpected_over_limit = [row for row in over_limit if row[0] != 24]
    if unexpected_over_limit:
        _fail(
            "sessions other than session 24 contain more than five questions: "
            f"{[(row[0], row[1]) for row in unexpected_over_limit]}"
        )

    session_24 = list(
        connection.execute(
            sa.text(
                """
                SELECT id, status
                FROM interview_sessions
                WHERE id = 24
                """
            )
        )
    )
    session_24_questions = list(
        connection.execute(
            sa.text(
                """
                SELECT id, answer, score, feedback
                FROM interview_questions
                WHERE session_id = 24
                ORDER BY created_at ASC, id ASC
                """
            )
        )
    )
    if session_24_questions and (
        not session_24
        or session_24[0][1] != "completed"
        or len(session_24_questions) != 6
    ):
        _fail("session 24 does not match the approved six-question historical case")
    if session_24_questions:
        archived_question = session_24_questions[-1]
        if (
            archived_question[1] is not None
            or archived_question[2] is not None
            or archived_question[3] is not None
        ):
            _fail("session 24 question 6 contains unexpected answer/evaluation data")

    orphan_questions = connection.execute(
        sa.text(
            """
            SELECT q.id
            FROM interview_questions q
            LEFT JOIN interview_sessions s ON s.id = q.session_id
            WHERE s.id IS NULL
            LIMIT 1
            """
        )
    ).first()
    if orphan_questions is not None:
        _fail(f"orphan interview question found: {orphan_questions[0]}")

    orphan_sessions = connection.execute(
        sa.text(
            """
            SELECT s.id
            FROM interview_sessions s
            LEFT JOIN users u ON u.id = s.user_id
            WHERE u.id IS NULL
            LIMIT 1
            """
        )
    ).first()
    if orphan_sessions is not None:
        _fail(f"orphan interview session found: {orphan_sessions[0]}")


def _validate_migrated_state(connection: sa.Connection) -> None:
    invalid_question_numbers = connection.execute(
        sa.text(
            """
            SELECT id, session_id, question_number
            FROM interview_questions
            WHERE question_number IS NOT NULL
              AND (question_number < 1 OR question_number > 5)
            LIMIT 1
            """
        )
    ).first()
    if invalid_question_numbers is not None:
        _fail(f"invalid question number after backfill: {invalid_question_numbers}")

    invalid_archived = connection.execute(
        sa.text(
            """
            SELECT id
            FROM interview_questions
            WHERE status = 'LEGACY_ARCHIVED'
              AND question_number IS NOT NULL
            LIMIT 1
            """
        )
    ).first()
    if invalid_archived is not None:
        _fail(f"archived question has a number: {invalid_archived[0]}")

    invalid_completed = connection.execute(
        sa.text(
            """
            SELECT s.id
            FROM interview_sessions s
            LEFT JOIN interview_questions q
              ON q.session_id = s.id
             AND q.question_number IS NOT NULL
            WHERE s.status = 'COMPLETED'
            GROUP BY s.id
            HAVING COUNT(q.id) <> 5
                OR COUNT(q.id) FILTER (
                    WHERE q.status NOT IN ('EVALUATED', 'LEGACY_EVALUATED')
                ) <> 0
            LIMIT 1
            """
        )
    ).first()
    if invalid_completed is not None:
        _fail(f"completed session violates the five-question invariant: {invalid_completed[0]}")

    invalid_active_count = connection.execute(
        sa.text(
            """
            SELECT session_id
            FROM interview_questions
            WHERE status IN ('ACTIVE', 'EVALUATING', 'EVALUATION_FAILED')
            GROUP BY session_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if invalid_active_count is not None:
        _fail(f"multiple active/in-flight questions in session: {invalid_active_count[0]}")


def upgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError(
            "This data-dependent migration must be executed online; offline SQL generation is unsupported."
        )

    connection = op.get_bind()
    _validate_source_state(connection)

    op.add_column(
        "interview_sessions",
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "interview_questions",
        sa.Column("question_number", sa.Integer(), nullable=True),
    )
    op.add_column(
        "interview_questions",
        sa.Column("status", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "interview_questions",
        sa.Column("evaluation", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "interview_questions",
        sa.Column("answer_submitted_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "interview_questions",
        sa.Column("evaluated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "interview_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("interview_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("interview_questions.id"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("from_status", sa.String(length=30), nullable=True),
        sa.Column("to_status", sa.String(length=30), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    connection.execute(
        sa.text(
            """
            UPDATE interview_sessions s
            SET updated_at = COALESCE(
                s.finished_at,
                (
                    SELECT MAX(q.created_at)
                    FROM interview_questions q
                    WHERE q.session_id = s.id
                ),
                s.started_at
            )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE interview_sessions
            SET status = CASE status
                WHEN 'in_progress' THEN 'IN_PROGRESS'
                WHEN 'completed' THEN 'COMPLETED'
                ELSE status
            END
            """
        )
    )
    connection.execute(
        sa.text(
            """
            WITH numbered AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY session_id
                           ORDER BY created_at ASC, id ASC
                       ) AS number
                FROM interview_questions
            )
            UPDATE interview_questions q
            SET question_number = numbered.number
            FROM numbered
            WHERE q.id = numbered.id
              AND NOT (q.session_id = 24 AND numbered.number = 6)
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE interview_questions
            SET question_number = NULL
            WHERE session_id = 24
              AND id = (
                  SELECT q2.id
                  FROM interview_questions q2
                  WHERE q2.session_id = 24
                  ORDER BY q2.created_at ASC, q2.id ASC
                  OFFSET 5 LIMIT 1
              )
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE interview_questions
            SET status = CASE
                WHEN session_id = 24
                 AND question_number IS NULL
                    THEN 'LEGACY_ARCHIVED'
                WHEN answer IS NOT NULL
                    THEN 'LEGACY_EVALUATED'
                ELSE 'ACTIVE'
            END,
                evaluation = NULL,
                answer_submitted_at = NULL,
                evaluated_at = NULL
            """
        )
    )

    connection.execute(
        sa.text(
            """
            ALTER TABLE interview_sessions
            ALTER COLUMN updated_at SET NOT NULL
            """
        )
    )
    connection.execute(
        sa.text(
            """
            ALTER TABLE interview_questions
            ALTER COLUMN status SET NOT NULL
            """
        )
    )

    op.create_check_constraint(
        "ck_interview_sessions_status",
        "interview_sessions",
        "status IN ('IN_PROGRESS', 'GENERATING', 'GENERATION_FAILED', 'READY_TO_FINISH', 'COMPLETED')",
    )
    op.create_check_constraint(
        "ck_interview_questions_number_range",
        "interview_questions",
        "question_number IS NULL OR question_number BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_interview_questions_archived_number",
        "interview_questions",
        "status <> 'LEGACY_ARCHIVED' OR question_number IS NULL",
    )
    op.create_check_constraint(
        "ck_interview_questions_status",
        "interview_questions",
        "status IN ('ACTIVE', 'EVALUATING', 'EVALUATION_FAILED', 'EVALUATED', 'LEGACY_EVALUATED', 'LEGACY_ARCHIVED')",
    )

    _validate_migrated_state(connection)

    op.create_index(
        "uq_interview_questions_session_number",
        "interview_questions",
        ["session_id", "question_number"],
        unique=True,
        postgresql_where=sa.text("question_number IS NOT NULL"),
    )
    op.create_index(
        "uq_interview_questions_one_active",
        "interview_questions",
        ["session_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('ACTIVE', 'EVALUATING', 'EVALUATION_FAILED')"
        ),
    )
    op.create_index(
        "ix_interview_sessions_user_status",
        "interview_sessions",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_interview_audit_log_session_created",
        "interview_audit_log",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError(
            "This data-dependent migration must be executed online; offline SQL generation is unsupported."
        )

    connection = op.get_bind()

    unsupported_status = connection.execute(
        sa.text(
            """
            SELECT status
            FROM interview_sessions
            WHERE status NOT IN ('IN_PROGRESS', 'COMPLETED')
            LIMIT 1
            """
        )
    ).first()
    if unsupported_status is not None:
        _fail(
            "downgrade cannot preserve session status "
            f"'{unsupported_status[0]}'"
        )

    op.drop_index("ix_interview_audit_log_session_created", table_name="interview_audit_log")
    op.drop_index("ix_interview_sessions_user_status", table_name="interview_sessions")
    op.drop_index("uq_interview_questions_one_active", table_name="interview_questions")
    op.drop_index("uq_interview_questions_session_number", table_name="interview_questions")

    op.drop_constraint(
        "ck_interview_questions_status",
        "interview_questions",
        type_="check",
    )
    op.drop_constraint(
        "ck_interview_questions_archived_number",
        "interview_questions",
        type_="check",
    )
    op.drop_constraint(
        "ck_interview_questions_number_range",
        "interview_questions",
        type_="check",
    )
    op.drop_constraint(
        "ck_interview_sessions_status",
        "interview_sessions",
        type_="check",
    )

    op.drop_table("interview_audit_log")
    op.drop_column("interview_questions", "evaluated_at")
    op.drop_column("interview_questions", "answer_submitted_at")
    op.drop_column("interview_questions", "evaluation")
    op.drop_column("interview_questions", "status")
    op.drop_column("interview_questions", "question_number")
    op.drop_column("interview_sessions", "updated_at")

    connection.execute(
        sa.text(
            """
            UPDATE interview_sessions
            SET status = CASE status
                WHEN 'IN_PROGRESS' THEN 'in_progress'
                WHEN 'COMPLETED' THEN 'completed'
                ELSE status
            END
            """
        )
    )
