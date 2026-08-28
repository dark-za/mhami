import yaml, sys

ok = True
for f in ["compose.yml", "compose.dev.yml", "compose.prod.yml"]:
    try:
        with open(f) as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as e:
        print(f, "YAML ERROR:", e)
        ok = False
        continue

    if f == "compose.yml":
        api = data.get("services", {}).get("api", {})
        db = data.get("services", {}).get("db", {})
        fe = data.get("services", {}).get("frontend", {})
        checks = [
            ("api user", api.get("user") == "1000:1000"),
            ("api cap_drop ALL", "ALL" in (api.get("cap_drop") or [])),
            ("api security_opt no-new-privileges", "no-new-privileges:true" in (api.get("security_opt") or [])),
            ("api pids_limit 100", api.get("pids_limit") == 100),
            ("api mem_limit 512m", api.get("mem_limit") == "512m"),
            ("api AUDIT_HMAC_SECRET", "AUDIT_HMAC_SECRET" in (api.get("environment") or {})),
            ("db user 999", db.get("user") == "999:999"),
            ("db cap_drop ALL", "ALL" in (db.get("cap_drop") or [])),
            ("fe cap_drop ALL", "ALL" in (fe.get("cap_drop") or [])),
        ]
    elif f == "compose.prod.yml":
        api = data.get("services", {}).get("api", {})
        worker = data.get("services", {}).get("worker", {})
        beat = data.get("services", {}).get("beat", {})
        certbot = data.get("services", {}).get("certbot", {})
        renew = data.get("services", {}).get("certbot-renew", {})
        checks = [
            ("api read_only true", api.get("read_only") is True),
            ("api tmpfs /tmp", any("/tmp" in t for t in (api.get("tmpfs") or []))),
            ("worker cap_drop ALL", "ALL" in (worker.get("cap_drop") or [])),
            ("worker read_only", worker.get("read_only") is True),
            ("beat read_only", beat.get("read_only") is True),
            ("certbot exists", bool(certbot)),
            ("certbot-renew exists", bool(renew)),
        ]
    else:
        checks = [("dev file present", True)]

    failed = [n for n, c in checks if not c]
    if failed:
        ok = False
        print(f, "FAILED:", failed)
    else:
        print(f, "ALL CHECKS PASSED ({} items)".format(len(checks)))

sys.exit(0 if ok else 1)
