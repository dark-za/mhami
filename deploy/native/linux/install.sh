#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/mhami}"
CONFIG_ROOT="${CONFIG_ROOT:-/etc/mhami}"
DATA_ROOT="${DATA_ROOT:-/var/lib/mhami}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

id mhami >/dev/null 2>&1 || useradd --system --home-dir "${APP_ROOT}" --shell /usr/sbin/nologin mhami
install -d -o mhami -g mhami "${APP_ROOT}" "${DATA_ROOT}"/{media,backups,backup-restores} /var/log/mhami
install -d -m 0750 -o root -g mhami "${CONFIG_ROOT}"

python3.13 -m venv "${APP_ROOT}/venv"
"${APP_ROOT}/venv/bin/pip" install --upgrade pip
"${APP_ROOT}/venv/bin/pip" install --requirement "${APP_ROOT}/backend/requirements.txt"

if [[ ! -f "${CONFIG_ROOT}/mhami.env" ]]; then
  install -m 0640 -o root -g mhami \
    "${APP_ROOT}/deploy/native/linux/mhami.env.example" \
    "${CONFIG_ROOT}/mhami.env"
  echo "Created ${CONFIG_ROOT}/mhami.env; replace all placeholder secrets before continuing." >&2
  exit 2
fi

cd "${APP_ROOT}/backend"
set -a
# shellcheck disable=SC1091
source "${CONFIG_ROOT}/mhami.env"
set +a
"${APP_ROOT}/venv/bin/python" manage.py upgrade

install -m 0644 "${APP_ROOT}/deploy/native/linux/systemd/"*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mhami-api.service mhami-worker.service mhami-beat.service
systemctl start mhami-api.service mhami-worker.service mhami-beat.service
