# Deploying for free

A public URL for this project at no cost, split across three free tiers:

| Piece | Host | Why |
| --- | --- | --- |
| Frontend | **Vercel** | Next.js is theirs; free tier, HTTPS and a domain included |
| Backend | **Hugging Face Spaces** (Docker) | free tier gives ~16 GB RAM, which the embedding model needs |
| Database | **Neon** | free managed PostgreSQL |

The backend is the awkward one. It loads a sentence-transformers model into
memory, so it needs roughly 1 GB of RAM at rest — more than the 512 MB most
free web tiers allow. Hugging Face is the exception, and it is the natural home
for a model-backed service anyway.

> **Verify as you go.** These providers change their dashboards and free-tier
> terms often, and the guide below was written without access to them. Treat
> the field names as a map, not gospel — if something is named differently on
> screen, follow the screen.

---

## Before you start

Have ready:

- A Google AI Studio (Gemini) API key, if you want real evaluations rather than
  the mock provider.
- A fresh `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Do **not** reuse the one from your local `.env`.

---

## 1. Database — Neon

1. Create a project at [neon.tech](https://neon.tech).
2. Copy the connection string. It looks like:
   ```
   postgresql://user:password@ep-something.region.aws.neon.tech/neondb?sslmode=require
   ```
3. Keep it. You do not need to edit it — `backend/database.py` rewrites a
   driver-less `postgresql://` URL to the psycopg v3 driver the project ships.

Migrations run by themselves: the container's entrypoint applies
`alembic upgrade head` before uvicorn starts, so the schema is created on the
first boot.

---

## 2. Backend — Hugging Face Spaces

### Create the Space

New Space → **Docker** SDK → blank template → CPU basic (free).

### Give it the code

The Space is its own git repository and expects a `Dockerfile` at its root,
which is where this project's backend Dockerfile lives.

It also reads its configuration from YAML frontmatter at the top of
`README.md`. This repo's README has none, and adding it would put a config
block at the top of the page people read on GitHub. Keep the two apart with a
branch that exists only for the Space:

```bash
git checkout -b hf-space
```

Add this to the very top of `README.md` on that branch, above everything else:

```yaml
---
title: AI Interview Agent
emoji: 🎯
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
---
```

Then commit and push it as the Space's main branch:

```bash
git add README.md && git commit -m "chore: Hugging Face Space configuration"
git remote add space https://huggingface.co/spaces/<your-user>/<space-name>
git push space hf-space:main
```

To ship changes later:

```bash
git checkout hf-space && git merge main && git push space hf-space:main
```

### Set the secrets

In the Space: **Settings → Variables and secrets**. Anything with a real value
goes in as a *secret*, not a variable.

| Name | Value |
| --- | --- |
| `DATABASE_URL` | the Neon connection string |
| `SECRET_KEY` | the fresh one you generated |
| `LLM_PROVIDER` | `gemini` (or `mock` to run without a key) |
| `GEMINI_API_KEY` | your key |
| `MODEL_NAME` | `gemini-2.0-flash` |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `TRUST_PROXY_HEADERS` | `true` |
| `CORS_ALLOW_ORIGINS` | your Vercel URL — fill in after step 3 |

`TRUST_PROXY_HEADERS=true` matters here: the Space sits behind a proxy, so
without it every visitor looks like the same caller and a single rate-limit
bucket throttles the whole site.

`APP_ENV=production` makes the app refuse to boot on an unsafe config — a
short `SECRET_KEY`, `DEBUG` left on, a missing database.

The first build is slow (it installs torch and bakes the embedding model into
the image). Watch the Space's build log.

---

## 3. Frontend — Vercel

1. Import the GitHub repository at [vercel.com](https://vercel.com).
2. **Root Directory: `frontend`** — without this the build fails, since the
   Next.js app is not at the repository root.
3. Environment variable:
   ```
   NEXT_PUBLIC_API_URL = https://<your-user>-<space-name>.hf.space
   ```
4. Deploy.

`NEXT_PUBLIC_*` values are compiled into the browser bundle, so changing this
one later needs a **redeploy**, not just a restart.

---

## 4. Introduce them

Go back to the Space and set `CORS_ALLOW_ORIGINS` to the Vercel URL, exactly —
scheme included, no trailing slash:

```
https://your-project.vercel.app
```

Restart the Space. Then open the Vercel URL, register, upload a CV, and run an
interview.

---

## What this free setup does not do

Worth knowing before you show it to anyone, and worth saying out loud in an
interview — knowing the limits of your own deployment is the point.

- **Uploads do not survive a restart.** CVs and the FAISS indexes are written
  to the container's own disk, which the free tier wipes when the Space
  restarts or wakes. Fine for a demo run end to end in one sitting; the real
  fix is object storage (S3, Cloudflare R2), and it is the first thing to do
  before this handles anyone's real data.
- **The Space sleeps** after a stretch of inactivity, so the first visit after
  a quiet period is slow while it wakes.
- **One instance only.** The rate limiter counts in process memory and the
  entrypoint migrates on boot; both assume a single container. Several replicas
  need shared state and a separate migration job.
- **The rate limiter is a cost guard, not a security control.** It caps how
  fast the LLM can be called. It is not a substitute for the platform's own
  protection, and it does not stop a determined attacker.
- **Gemini's free tier has its own quota.** The global limit
  (`RATE_LIMIT_GLOBAL_EXPENSIVE_PER_MINUTE`) is what keeps a single visitor
  from spending all of it; lower it if you would rather be cautious.

---

## Sanity checks

```bash
# Backend is up and its database is migrated
curl https://<your-user>-<space-name>.hf.space/health

# Rate limiting is live (the 11th call in a minute should be 429)
for i in $(seq 1 11); do
  curl -s -o /dev/null -w "%{http_code} " \
    -X POST https://<your-user>-<space-name>.hf.space/login \
    -H "Content-Type: application/json" -d '{"email":"a@b.c","password":"x"}'
done; echo
```

If the backend answers but the frontend cannot reach it, it is almost always
`CORS_ALLOW_ORIGINS` — check it against the browser console, which names the
origin it expected.
