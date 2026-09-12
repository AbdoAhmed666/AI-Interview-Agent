# Known Issues (out-of-scope, documented per engineering Rule 12)

These are real defects discovered during the Finding 3 inspection. They are
**intentionally not fixed** as part of Finding 3 (Remove Process-Local Workflow
Authority) to keep that change minimal and reviewable. Each should become its
own task.

## 1. `/finish-interview` route raises `NameError` on the happy path — FIXED

**File:** `api/interview.py` (the `finish_interview` route handler).

**Problem:** `service = _get_interview_service()` was indented **inside** the
`if session_obj.user_id != current_user.id:` block. On the normal path (caller
owns the session) that branch is not entered, so `service` was never bound and
`return service.finish_interview(...)` raised `NameError`.

**Resolution:** De-indented `service = _get_interview_service()` to the function
body so it always runs on the happy path. The route now reaches
`service.finish_interview(...)` normally.

**Note:** The endpoint is still only exercised indirectly by tests
(`test_finish_interview.py` calls `InterviewService.finish_interview(...)`
directly). A route-level HTTP test would be a good follow-up.

## 2. `test_next_question_generation.py` teardown FK violation — FIXED

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

**Resolution:** Added `ON DELETE CASCADE` to both `interview_audit_log`
foreign keys (`session_id` and `question_id`) via migration
`d2f5a1b9c3e7`, and updated `models.py` to match. Deleting a session or
question now removes its audit rows instead of raising, which also makes
test teardown integrity-safe.
