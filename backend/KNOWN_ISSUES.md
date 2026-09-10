# Known Issues (out-of-scope, documented per engineering Rule 12)

These are real defects discovered during the Finding 3 inspection. They are
**intentionally not fixed** as part of Finding 3 (Remove Process-Local Workflow
Authority) to keep that change minimal and reviewable. Each should become its
own task.

## 1. `/finish-interview` route raises `NameError` on the happy path

**File:** `api/interview.py` (the `finish_interview` route handler).

**Problem:** `service = _get_interview_service()` is indented **inside** the
`if session_obj.user_id != current_user.id:` block. On the normal path (caller
owns the session) that branch is not entered, so `service` is never bound and
`return service.finish_interview(...)` raises `NameError`.

**Impact:** The finish HTTP endpoint is broken in the running app. It is not
caught by tests because `test_finish_interview.py` calls
`InterviewService.finish_interview(...)` directly and bypasses the route.

**Fix:** De-indent `service = _get_interview_service()` to the function body
(one line). This is the same class of indentation bug that the uncommitted
working-tree diff fixed inside `services/interview_service.py`.

## 2. `test_next_question_generation.py` teardown FK violation

**File:** `test_next_question_generation.py` — `_clear_test_rows`.

**Problem:** Teardown deletes `interview_questions` rows where
`question_number > 3`, but only deletes four audit event types
(`GENERATION_STARTED`, `GENERATION_SUCCEEDED`, `GENERATION_FAILED`,
`INTERVIEW_READY_TO_FINISH`). Other audit rows that reference those questions
(`ANSWER_SUBMITTED`, `EVALUATION_*`, `GENERATION_RETRY_*`) are left behind, and
`interview_audit_log.question_id` has no `ON DELETE CASCADE`, so deleting the
questions raises `ForeignKeyViolation`.

**Note:** The handoff attributed this to `crud.delete_questions_after`. That
function does not exist; the failing deletion is inline in the test teardown.

**Fix options (pick in its own task):** delete referencing audit rows first in
teardown, or add `ON DELETE CASCADE`/`SET NULL` to the
`interview_audit_log.question_id` FK via an Alembic migration.
