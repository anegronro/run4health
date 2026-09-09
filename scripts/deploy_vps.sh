#!/usr/bin/env bash
# Copies the app to a server and (re)starts it under systemd.
#
# Your own addresses go in scripts/deploy.env, which is git-ignored — see
# deploy.env.example. Nothing about your server belongs in this repository.
set -euo pipefail

cd "$(dirname "$0")/.."
[ -f scripts/deploy.env ] && . scripts/deploy.env

HOST="${FITNESS_HOST:-}"
BIND="${FITNESS_BIND:-127.0.0.1}"
PORT="${FITNESS_PORT:-8770}"
URL="${FITNESS_URL:-http://$BIND:$PORT}"
REMOTE="${FITNESS_REMOTE:-/opt/fitness-app}"

if [ -z "$HOST" ]; then
  echo "Set FITNESS_HOST — copy scripts/deploy.env.example to scripts/deploy.env" >&2
  exit 1
fi

echo "→ copying source to $HOST:$REMOTE"
ssh "$HOST" "mkdir -p $REMOTE"
rsync -az --delete \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
  --exclude '.DS_Store' --exclude '.claude' \
  --exclude 'data/app.db' --exclude 'data/app.db-wal' --exclude 'data/app.db-shm' \
  --exclude 'data/*.json' --exclude 'data/*.json.tmp' --exclude 'data/*.migrated' \
  ./ "$HOST:$REMOTE/"

echo "→ installing dependencies"
ssh "$HOST" "cd $REMOTE && python3 -m venv --upgrade-deps .venv >/dev/null && \
  .venv/bin/pip install -q 'fastapi>=0.115' 'uvicorn[standard]>=0.32' 'jinja2>=3.1' 'pydantic>=2.9'"

echo "→ installing the nightly backup"
ssh "$HOST" "mkdir -p /var/backups/fitness && \
  ( crontab -l 2>/dev/null | grep -v 'fitness-app/scripts/backup.sh' ; \
    echo '17 4 * * * $REMOTE/scripts/backup.sh >> /var/log/fitness-backup.log 2>&1' ) | crontab -"

echo "→ writing unit file"
ssh "$HOST" "cat > /etc/systemd/system/fitness.service <<UNIT
[Unit]
Description=fitness-app (training program catalogue)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$REMOTE
# Shared password for the public URL. Lives only on the server, never in git.
EnvironmentFile=-/etc/fitness.env
ExecStart=$REMOTE/.venv/bin/uvicorn app.main:app --host $BIND --port $PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload && systemctl enable --now fitness.service && systemctl restart fitness.service"

sleep 2
echo "→ health check"
ssh "$HOST" "systemctl is-active fitness.service && curl -sf http://$BIND:$PORT/health"
echo
echo "Live at $URL"
