#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?Set DATABASE_URL first}"
mkdir -p db/dumps
pg_dump "$DATABASE_URL" > "db/dumps/$(date +%Y%m%d)_backup.sql"
echo "Dump written to db/dumps/"
