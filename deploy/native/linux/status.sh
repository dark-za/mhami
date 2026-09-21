#!/usr/bin/env bash
set -euo pipefail

systemctl --no-pager --full status mhami-api.service mhami-worker.service mhami-beat.service
