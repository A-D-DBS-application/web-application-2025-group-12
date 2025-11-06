#!/usr/bin/env bash
# Safe DB re-create script for local Postgres (destructive)
# Usage:
#   export PGHOST=... PGUSER=... PGDATABASE=... PGPORT=... (or set PGPASSWORD)
#   bash scripts/recreate_db.sh

set -euo pipefail

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found. Please install PostgreSQL client tools or run this on a machine with psql."
  exit 1
fi

echo "This script will DROP the application tables and re-run db/schema.sql."
echo "Make sure you have a backup if you need the current data."
read -p "Type RECREATE to continue (or anything else to abort): " CONFIRM
if [[ "$CONFIRM" != "RECREATE" ]]; then
  echo "Aborted. No changes made."
  exit 0
fi

echo "Running destructive reinit against: ${PGHOST:-localhost}/${PGDATABASE:-<unknown>} as ${PGUSER:-$(whoami)}"

# Drop tables in dependency order (matches -> preferences -> ground -> client -> company)
echo "Dropping tables..."
psql -v ON_ERROR_STOP=1 <<'SQL'
DROP TABLE IF EXISTS public.match CASCADE;
DROP TABLE IF EXISTS public.preferences CASCADE;
DROP TABLE IF EXISTS public.ground CASCADE;
DROP TABLE IF EXISTS public.client CASCADE;
DROP TABLE IF EXISTS public.company CASCADE;
SQL

echo "Recreating schema from db/schema.sql..."
psql -v ON_ERROR_STOP=1 -f db/schema.sql

echo "Schema re-created successfully."
echo "You may now (re)run your seed scripts or the app to repopulate test data."

exit 0
