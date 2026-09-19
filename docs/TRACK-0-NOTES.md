# Track 0 — one request, end to end

Session record. What was established, what is still open, and where the next
session picks up. Companion to `LEARNING.md`; the protocol lives there.

---

## The chain, and what each layer is allowed to know

One click on **Submit Answer**:

| # | Layer | Owns | Must not know |
| --- | --- | --- | --- |
| 1 | `components/interview/AnswerEditor.tsx` | The textarea, the button, when the button is disabled | That a server exists |
| 2 | `contexts/InterviewContext.tsx` | Calls the hook **once**, shares that one instance | Anything about interviews |
| 3 | `hooks/useInterview.ts` | The state, `submit()`, what the screen should show next | HTTP, URLs, tokens |
| 4 | `services/interview.service.ts` | The path, and camelCase → snake_case | React, state |
| 5 | `lib/axios.ts` | `baseURL`, the auth header, the 401 response | What any request means |
| — | **the network boundary** | — | — |
| 6 | `main.py` | App wiring, CORS middleware, `lifespan` validation | Business rules |
| 7 | `api/interview.py` | HTTP in, HTTP out: reads the body, maps exceptions to status codes | How anything is computed |
| 8 | `services/interview_service.py` | The rules, the transactions, the authority | That HTTP exists |
| 9 | `repositories/interview_repository.py` | SQL only; never commits, never closes | Why it is being asked |
| 10 | PostgreSQL | The truth | — |

`LEARNING.md` originally drew this as seven hops. It is ten: the Context, the
service module, and PostgreSQL itself were missing. The chain there is fixed.

## What was established

**State lives in one place, on purpose.** `useInterview()` calls `useState`
fourteen times. Call that hook from three components and you get three
independent copies — submitting in one would not update the others. The
Provider calls it once and hands the same instance down. `useInterview()` from
the context throws if used outside the Provider: fail loudly rather than
silently render empty state.

**`loading` is a lock, not a decoration.** `setLoading(true)` is what drives
`disabled={loading || ...}` on the button, which is what stops a double submit.
`setLoading(false)` sits in `finally`, not at the end of `try` — on an error the
button must come back, or the user is stuck on a dead screen.

**The client guesses; the server decides.** In `submit()`:

```ts
const isFinished =
  data?.status === "READY_TO_FINISH" ||
  (questionNumber >= totalQuestions && Boolean(data?.evaluation));
```

The second branch is the browser counting for itself. Tamper with
`questionNumber` in DevTools and the UI will claim the interview is over — but
`finish_interview` re-reads the row under `SELECT ... FOR UPDATE` and raises
`FinishConflict` unless the status really is `READY_TO_FINISH`. So the damage is
a screen that lies, not data that moves. Same family as the dashboard bug in
`LEARNING.md`'s third story: a screen that computes instead of asking.

**Nothing crosses the boundary without being re-checked.** The route is clean —
no header parsing, no token decoding. `Depends(get_current_user)` runs first and
raises 401 before the first line of the body executes. Ownership is then
checked *again* in the service (`session.user_id != user_id`), because the
service must hold on its own, whatever route called it.

**Build time vs run time.** `baseURL` comes from `NEXT_PUBLIC_API_URL`, which
Next.js bakes into the client bundle during `npm run build`. Changing the env
var and restarting changes nothing; it needs a rebuild. In
`docker-compose.yml` it is passed under `build.args`, not `environment` — and
its value is `http://localhost:8000`, not `http://backend:8000`, because the
browser resolves it, not the container. `DATABASE_URL` is the opposite: read at
run time, no rebuild needed.

## Open findings

**`Depends(get_db)` in `/adaptive-interview` is unused.** The parameter is
declared; `db` never appears in the body. `get_db` opens a real
`SessionLocal()` and closes it in `finally`, so every request to this route
pays for a connection nobody reads, while the service opens its own sessions.
Decide: drop the parameter, or push the route's session down into the service.

**The `||` fallback in `submit()`.** Keep it and accept a screen that can lie,
or drop it and let `READY_TO_FINISH` be the only signal. Worth an ADR.

## Still open in Track 0

- The route body: why three service calls (`claim_answer`,
  `evaluate_claimed_answer`, `generate_next_question`) instead of one, and
  which of them touches the LLM.
- The trip back up: how the response becomes the next question card.
- The exercise: a log line at each layer, one submission, read the order.
- CORS: does it protect the server or the user? (`curl` ignores it entirely.)
