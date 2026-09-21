#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/mhami}"
CONFIG_ROOT="${CONFIG_ROOT:-/etc/mhami}"
DATA_ROOT="${DATA_ROOT:-/var/lib/mhami}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this uninstaller as root." >&2
  exit 1
fi
if [[ "${1:-}" != "REMOVE-MHAMI-DATA" ]]; then
  echo "Refusing to remove data. Re-run with REMOVE-MHAMI-DATA after taking a backup." >&2
  exit 2
fi

systemctl disable --now mhami-api.service mhami-worker.service mhami-beat.service || true
rm -f /etc/systemd/system/mhami-api.service /etc/systemd/system/mhami-worker.service /etc/systemd/system/mhami-beat.service
systemctl daemon-reload
rm -rf -- "${APP_ROOT}" "${CONFIG_ROOT}" "${DATA_ROOT}"
