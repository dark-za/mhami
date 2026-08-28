# k6 Load Tests

The scenarios in this directory drive the workspace API under
realistic load. They are designed to be run against a staging or
production-equivalent environment — never against production.

## Prerequisites

1. **k6** — `winget install k6 --source winget` (Windows), `brew
   install k6` (macOS), or `apt install k6` (Linux).
2. A populated workspace — the `make_load_users` management command
   seeds the user pool.

## Usage

```bash
cd backend
python manage.py make_load_users --per-role 50

# Run the API load scenario
k6 run tests/load/api_load.js

# Run the evidence load scenario
k6 run tests/load/evidence_load.js

# Run the reviews load scenario
k6 run tests/load/reviews_load.js
```

## Thresholds

Every scenario declares the same SLOs:

- `http_req_duration` p(95) < 500 ms
- `http_req_failed` rate < 1 %

The thresholds are non-negotiable. A regression that pushes the
p(95) above 500 ms fails the CI step.

## Configuration

| Environment variable | Default | Purpose |
|---|---|---|
| `API_URL` | `http://localhost:8000` | Base URL of the API under test |
| `API_VUS` | `100` | Number of virtual users |
| `API_DURATION` | `5m` | Duration of the sustained phase |
