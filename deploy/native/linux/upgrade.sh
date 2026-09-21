#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/mhami}"
VENV="${APP_ROOT}/venv"
BACKEND="${APP_ROOT}/backend"

cd "${BACKEND}"
"${VENV}/bin/pip" install --requirement requirements.txt
"${VENV}/bin/python" manage.py upgrade
systemctl restart mhami-api.service mhami-worker.service mhami-beat.service
systemctl --no-pager --full status mhami-api.service mhami-worker.service mhami-beat.service
