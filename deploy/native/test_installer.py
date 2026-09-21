from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("installer.py")
SPEC = importlib.util.spec_from_file_location("mhami_native_installer", MODULE_PATH)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def test_bootstrapper_creates_production_environment_without_plaintext_defaults(tmp_path):
    args = argparse.Namespace(
        mode="standalone",
        hostname="localhost",
        env_file=tmp_path / "mhami.env",
        data_root=tmp_path / "data",
        postgres_host="127.0.0.1",
        postgres_port=5432,
        postgres_db="platform",
        postgres_user="platform",
        postgres_password="database-secret",
        redis_url="redis://127.0.0.1:6379/0",
        backup_external_uri="s3://approved-bucket/mhami/",
        workers=1,
        concurrency=1,
        force=False,
    )
    values = installer.build_values(args)
    installer._write_env(args.env_file, values, force=False)
    content = args.env_file.read_text(encoding="utf-8")
    assert "DJANGO_SECRET_KEY=change-me" not in content
    assert "BACKUP_EXTERNAL_URI=s3://approved-bucket/mhami/" in content
    assert "BACKUP_EXTERNAL_KEYS=" in content


def test_bootstrapper_does_not_overwrite_existing_environment(tmp_path):
    path = tmp_path / "mhami.env"
    path.write_text("KEEP=1\n", encoding="utf-8")
    try:
        installer._write_env(path, {"NEW": "2"}, force=False)
    except RuntimeError as exc:
        assert "Refusing to overwrite" in str(exc)
    else:
        raise AssertionError("Existing environment file was overwritten")
