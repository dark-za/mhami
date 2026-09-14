# Mhami Organization Connector

The connector is a small FastAPI service that runs inside a self-hosted organization's environment. Mhami sends signed requests to the connector, and the connector forwards allowed AI analysis jobs to the organization's chosen private or local AI provider.

## Security Model

- Requires `CONNECTOR_API_KEY`; the service refuses to start without it.
- Verifies `x-mhami-signature`, `x-mhami-timestamp`, and `x-mhami-nonce`.
- Uses HMAC signing and replay protection.
- Runs as a non-root user in the Docker image.
- Exposes `/health`, `/ready`, and `/v1/ai/analyze`.

## Local Run

```bash
cp connector/config/example.env connector/config/local.env
docker build -t mhami-connector ./connector
docker run --env-file connector/config/local.env -p 8088:8088 mhami-connector
```

## Test Suite

Install the declared test extra, then run the local test suite:

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

The tests verify:
- Signature round-trip with freshness checking
- Missing signature rejection
- Tampered body rejection
- Stale timestamp rejection
- Replay protection
- Secret loading validation

The connector is a boundary component. Production deployments should source `CONNECTOR_API_KEY` from the operating organization's secret manager and restrict inbound network access to the Mhami platform.
