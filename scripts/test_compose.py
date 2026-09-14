"""Check resolved Compose contracts without starting containers or reading .env."""

import json
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def compose_config(override):
    env = {key: value for key, value in os.environ.items() if not key.startswith("COMPOSE_")}
    env.update({
        "DJANGO_SECRET_KEY": "compose-validation-only-not-for-deployment",
        "AUDIT_HMAC_SECRET": "compose-validation-only-not-for-deployment",
        "DJANGO_ALLOWED_HOSTS": "example.invalid",
        "POSTGRES_PASSWORD": "compose-validation-only-not-for-deployment",
        "METRICS_TOKEN": "compose-validation-only-not-for-deployment",
        "BACKUP_ENCRYPTION_KEY": "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
    })
    result = subprocess.run(
        ["docker", "compose", "--env-file", os.devnull, "-f", "compose.yml",
         "-f", override, "config", "--format", "json"],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True, timeout=60,
    )
    if result.returncode:
        raise RuntimeError(f"Compose validation failed: {result.stderr}")
    return json.loads(result.stdout)["services"]


class ComposeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dev = compose_config("compose.dev.yml")
        cls.prod = compose_config("compose.prod.yml")

    def test_development_ports_are_loopback_only(self):
        for name, service in self.dev.items():
            for port in service.get("ports", []):
                with self.subTest(service=name, port=port["target"]):
                    self.assertEqual(port.get("host_ip"), "127.0.0.1")

    def test_development_frontend_waits_for_api_health(self):
        self.assertEqual(
            self.dev["frontend"]["depends_on"]["api"]["condition"], "service_healthy",
        )

    def test_development_ports_and_internal_proxy_are_preserved(self):
        for name, target in {"api": 8000, "frontend": 5173, "db": 5432, "redis": 6379}.items():
            with self.subTest(service=name):
                self.assertEqual([port["target"] for port in self.dev[name]["ports"]], [target])
        self.assertEqual(
            self.dev["frontend"]["environment"]["VITE_API_PROXY_TARGET"], "http://api:8000",
        )

    def test_production_only_publishes_frontend(self):
        for name in ("api", "db", "redis", "worker", "beat"):
            with self.subTest(service=name):
                self.assertFalse(self.prod[name].get("ports"))
        self.assertEqual({port["target"] for port in self.prod["frontend"]["ports"]}, {80, 443})
        self.assertEqual(self.prod["api"]["environment"]["DJANGO_DEBUG"], "false")


if __name__ == "__main__":
    unittest.main()
