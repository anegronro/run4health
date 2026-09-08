#!/usr/bin/env bash
# Nightly copy of the database, kept for two weeks.
#
# Uses sqlite3's own .backup, which takes a consistent snapshot of a live
# database — copying the file with cp while the app is writing can capture a
# half-written page. Every copy is checked before the old ones are pruned,
# because a backup nobody verified is a rumour.
set -euo pipefail

DB="${FITNESS_DB:-/opt/fitness-app/data/app.db}"
DEST="${FITNESS_BACKUPS:-/var/backups/fitness}"
KEEP_DAYS="${FITNESS_KEEP_DAYS:-14}"

mkdir -p "$DEST"
stamp=$(date +%F-%H%M)
out="$DEST/app-$stamp.db"

sqlite3 "$DB" ".backup '$out'"

# Refuse to prune unless this copy actually opens and reads clean.
if [ "$(sqlite3 "$out" 'PRAGMA integrity_check;')" != "ok" ]; then
  echo "backup failed integrity check: $out" >&2
  exit 1
fi
people=$(sqlite3 "$out" 'SELECT COUNT(*) FROM people;')
ticks=$(sqlite3 "$out" 'SELECT COUNT(*) FROM done;')

gzip -f "$out"
find "$DEST" -name 'app-*.db.gz' -mtime "+$KEEP_DAYS" -delete

echo "$(date -Is) ok $out.gz — $people people, $ticks ticks"
