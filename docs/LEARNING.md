# Learning map

A study plan for this codebase, kept in the repository so it survives between
sessions. Work through it with an AI assistant that can open the files.

---

## How to run a session

**Paste this at the start of a new session:**

> Open `docs/LEARNING.md` and let's do Track N. Follow the teaching protocol in
> that file: ask me first, don't explain before I answer.

### Teaching protocol

The point is not to be told how this works. It is to be able to explain it
without looking. So every topic runs in this order:

1. **Short setup** — the assistant explains the concept in the abstract, a few
   minutes, no code.
2. **Predict** — the assistant names a file and a function and asks *"what do
   you think this does, and why is it written this way?"* **Answer before
   opening it.** Being wrong here is the useful part.
3. **Check** — open the real file together and compare.
4. **Break it** — change something so a test fails, read the failure, put it
   back. A concept you have watched fail is a concept you own.
5. **Write** — one short paragraph in your own words. If it is a decision, it
   becomes an ADR (see below).

Rules for the assistant:

- Ask before you explain. Do not answer your own question.
- If an answer is wrong, do not correct it immediately — ask a narrower
  question that makes the gap visible.
- Prefer "run this and tell me what happens" over "here is what happens".
- Never write the learner's ADR for them. Edit what they wrote instead.

Discussion can be in any language; what goes in `docs/` is English, to match
the rest of the repository.

---

## Track 0 — One request, end to end

**Goal:** a map of the system before any of the details. One session.

Follow a single click on **Submit Answer** all the way down and back:

```
frontend/components/interview/AnswerEditor.tsx
  → frontend/hooks/useInterview.ts          submit()
  → frontend/lib/axios.ts                   the request leaves the browser
  → backend/main.py                         app setup, CORS middleware
  → backend/api/interview.py                /adaptive-interview
  → backend/services/interview_service.py
  → backend/repositories/interview_repository.py
  → PostgreSQL
```

**You should be able to answer:**

- Where does the browser learn the backend's address, and when is that decided?
- What does `Depends(get_current_user)` do before the route body runs?
- Why does the route call three service methods instead of one?
- Which of those three touches the LLM, and which only touch the database?
- Where does the response turn back into what the question card shows?

**Exercise:** add a `print` (or a log line) at each of the seven layers, submit
one answer, and read the order they fire in. Remove them afterwards.

---

## Track 1 — Backend and data

**Goal:** the layer you said you are weakest in. Expect several sessions.

**Files:** `backend/database.py` · `backend/models.py` ·
`backend/repositories/interview_repository.py` ·
`backend/services/interview_service.py` · `backend/api/interview.py` ·
`backend/alembic/versions/`

### 1a. Layers

- What does each of `api/`, `services/`, `repositories/` know about, and what
  is it forbidden to know about?
- `repositories/interview_repository.py` never calls `commit()`. Find the
  docstring that says why, and explain the rule to yourself.
- What breaks if a repository function opens its own session?

### 1b. Sessions and transactions

- What is a SQLAlchemy `Session`, and what does `SessionLocal()` hand you?
- `flush()` versus `commit()` — what does each one guarantee?
- `with db.begin():` — what happens to the writes inside it when an exception
  is raised halfway through?
- Why does `start_interview` create the session row *and* question 1 inside one
  `with db.begin()` instead of two?

### 1c. Concurrency — the heart of this project

- What problem does `SELECT ... FOR UPDATE` solve? Name a concrete sequence of
  two requests that goes wrong without it.
- When is a row lock the wrong tool?
- Read `_claim_evaluation_retry`. What is the "staleness lease", what happens
  if it is never refreshed, and what happens if it is too short?
- Why is the interview's state in PostgreSQL rather than in a dictionary on the
  server? What exactly broke when it lived in memory?
- Idempotency: what does `claim_answer` do when the same answer arrives twice,
  and why is that not the same as ignoring the second one?

### 1d. Migrations

- What is a migration, and why not let SQLAlchemy create the tables?
- Open `f3b6d0c8a91e_add_abandoned_session_status.py`. Why does its
  `downgrade()` update rows *before* restoring the constraint?
- What would happen on deploy if a migration were not idempotent?

**Exercise:** delete the `with_for_update()` from
`get_session_for_update`, run `pytest -q`, and read what fails. Put it back.

**Bonus (real cleanup):** `backend/analytics.py`, `backend/dependencies.py` and
`backend/pkg.py` are imported by nothing. Prove it for yourself, then decide
whether they should be deleted — and defend the answer either way.

---

## Track 2 — The AI pipeline

**Goal:** the part that makes this an AI project rather than a CRUD app.

**Files:** `backend/rag/` (all of it) · `backend/cv/` ·
`backend/evaluator.py` · `backend/llm_provider.py` ·
`backend/adaptive_engine.py` · `backend/prompts.py` · `backend/schemas.py`

### 2a. The pipeline

Put these in order and say what each one turns into what:

`parser` → `chunker` → `embeddings` → `vector_store` → `retriever` →
`query_builder` → `prompt_builder` → LLM → `schemas` validation

### 2b. Embeddings and retrieval

- What *is* an embedding? What does "close together" mean in that space?
- Why `BAAI/bge-small-en-v1.5` and not a larger model? What is the trade?
- Why chunk the CV at all? What does `CHUNK_OVERLAP` prevent?
- What does FAISS do that a `WHERE ... LIKE` cannot?
- Why retrieve from the CV *and* a role knowledge base separately, then
  combine?

### 2c. The leak (read this one closely)

`rag_service.py` used to hold one vector store on the service object.

- Construct the exact sequence of two users that leaks one CV into the other's
  interview.
- What does `ensure_cv_store` / `retrieve_hybrid_isolated` change about that?
- Why is a lock per directory needed on top of that?
- What class of bug is this, and why do tests rarely catch it by accident?

### 2d. Talking to a model

- Why does `evaluate_answer` return a validated `EvaluationResponse` instead of
  the model's text?
- What happens when the model returns something that does not fit the schema?
  Follow it to `EVALUATION_FAILED` and back.
- Why is there a `MockLLMProvider`, and what would the test suite look like
  without one?
- `adaptive_engine.py`: what decides the next question's difficulty?

### 2e. Alternatives

For each, what else exists and when would you switch:
FAISS vs pgvector vs Qdrant · a local embedding model vs an embeddings API ·
RAG vs stuffing the whole CV into the prompt · Gemini vs Groq vs a local model.

---

## Track 3 — Testing

**Goal:** the second gap. Aim for taste, not coverage numbers.

**Files:** `backend/conftest.py` · `backend/test_evaluation_persistence.py` ·
`backend/test_adaptive_interview_route.py` · `backend/test_answer_claim.py` ·
`frontend/hooks/__tests__/useInterview.test.tsx`

- Why write tests? The honest answer is not "quality" — find a better one.
- What makes a test *hermetic*? Why did this suite's tests fail on any machine
  but one, before `conftest.py`?
- **The teeth method:** revert a fix, confirm its test fails, restore it. Do
  this once yourself, with any fix in the git history. A test that passes with
  the fix removed is testing nothing.
- What is a fixture? What does `monkeypatch` actually replace, and when is it
  the wrong tool?
- Read `test_answer_claim.py::test_same_answer_duplicate_returns_persisted_state`
  and, right below it, `test_conflicting_duplicate_is_rejected`. They send the
  same request twice and expect opposite outcomes. What behaviour would be
  wrong if only the first of the two existed?

### What tests could not catch

Both of these are in the git history. Read the commits.

- **The 409.** Every first answer submission failed, while every test passed.
  Why did the suite not see it? What kind of test would have?
- **The CRLF shebang.** CI was green, the container would not boot on Windows.
  What is the general lesson about what CI proves?

---

## Track 4 — Containers and deployment

**Goal:** the third gap.

**Files:** `backend/Dockerfile` · `frontend/Dockerfile` ·
`docker-compose.yml` · `backend/docker-entrypoint.sh` ·
`.dockerignore` · `.github/workflows/ci.yml`

- Image, container, layer — define each, then explain why the order of lines in
  a Dockerfile changes build time.
- Why does the backend Dockerfile have two `FROM` lines?
- Why is the embedding model downloaded at *build* time? What does
  `HF_HUB_OFFLINE=1` prove about whether it worked?
- What does a healthcheck do for `depends_on`, and what did it prevent the
  night the backend would not boot?
- Migrations in the entrypoint: what does it buy, what does it cost with more
  than one replica?
- `.dockerignore`: why `**/.env` and not `.env`?
- Why must `NEXT_PUBLIC_API_URL` be known at build time, when `DATABASE_URL`
  need not be?

**Exercise:** `docker compose up -d`, then `docker compose exec backend sh` and
look around inside the container. Find the model cache. Confirm the app is not
running as root.

---

## Track 5 — Decisions and alternatives

Not a reading track — this is where the writing happens. One ADR per decision
(template below). Candidates, roughly in order of how interesting they are:

| # | Decision |
| --- | --- |
| 1 | PostgreSQL as the authority for interview state |
| 2 | Per-request isolated vector stores |
| 3 | FAISS over a vector database |
| 4 | A validated schema for model output |
| 5 | The embedding model baked into the image |
| 6 | Migrations in the container entrypoint |
| 7 | JWT in localStorage — and why it should change |

---

## Not built yet

These were on the original map but have no code behind them. Left here on
purpose: each is a track that starts by *building* the thing, and only then
writing the ADR. Do not send a reading session after them.

- **Rate limiting.** There is no `backend/rate_limit.py` and no rate limiting
  anywhere in the backend — nothing in the request path between CORS and the
  route. The questions worth answering once it exists: why two limits instead
  of one, which one actually caps the LLM bill, why the other can be walked
  around, and why a rejected request must not count against the limit it was
  rejected by. ADR candidate: *two rate limits instead of one*.
- **A deployment target.** There is no `DEPLOY.md`; `docker-compose.yml` is the
  whole deployment story today, and the README still lists production
  deployment under "next improvements". ADR candidate once a host is chosen:
  *where the backend runs, and why not the others*.

---

## Writing it down

### ADRs

One file per decision, `docs/adr/NNN-short-title.md`:

```markdown
# ADR-00N: <decision in one line>

## Status
Accepted — <date>

## Context
What was true that forced a choice. No solutions yet.

## Options considered
1. <option> — what it buys, what it costs
2. <option> — ...
3. <option> — ...

## Decision
What we chose, and the reason that actually decided it.

## Consequences
What is better now. What is worse or newly possible to get wrong.
What would make us revisit this.
```

Keep them short. One page. The "Options considered" section is the valuable
part — anyone can say what they built, few can say what they rejected.

### Publishing

Do **not** write one post per track; nobody reads that. Extract three stories
once the ADRs exist:

1. **The leak** — one shared object, two users, one CV in the wrong interview.
2. **The request that conflicted with itself** — a 409 on every first
   submission, and a full test suite that never noticed.
3. **Green tests, broken app** — the dashboard reporting zero completed
   interviews while listing completed interviews with their scores, and a
   carriage return that stopped a container from booting.

The third is the strongest, because the gap between "tests pass" and "it works"
is what separates someone who writes code from someone who ships it.

---

## Progress

| Track | Status | Notes |
| --- | --- | --- |
| 0 — One request end to end | not started | |
| 1 — Backend and data | not started | |
| 2 — The AI pipeline | not started | |
| 3 — Testing | not started | |
| 4 — Containers and deployment | not started | |
| 5 — ADRs | not started | |

Update the row at the end of each session, and note anything that stayed
unclear so the next session starts there.

---

## The bar

You are done with a track when you can explain it out loud, to someone else,
without opening the file. Not when you have read it.
