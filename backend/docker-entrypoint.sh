#!/bin/sh
# Bring the schema up to date, then hand over to the process in CMD.
set -e

# PostgreSQL is the authority for interview state, so the schema has to be
# current before the API serves a single request. `upgrade head` is idempotent:
# a container restarting against an already-migrated database is a no-op.
#
# This is deliberately simple and suits one API container. Running several
# replicas means several containers racing to migrate on deploy; point them at
# a one-shot migration job instead and drop this step.
echo "[entrypoint] applying database migrations..."
alembic upgrade head
echo "[entrypoint] migrations applied; starting: $*"

exec "$@"
