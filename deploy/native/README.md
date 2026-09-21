# Native deployment

This directory contains the direct-install foundation for Linux and Windows.
It is intentionally separate from the Docker Compose topology so an operator
can choose one runtime without changing application code.

## Linux

1. Install Python 3.13, PostgreSQL, Redis, NGINX, and Git from the operating
   system repositories or approved packages.
2. Place the release at `/opt/mhami`.
3. Copy `linux/mhami.env.example` to `/etc/mhami/mhami.env`, replace every
   placeholder, and protect the file with mode `0640`.
4. Run `linux/install.sh` as root.
5. Copy `linux/nginx/mhami.conf`, replace the hostname, install the TLS
   certificate, and reload NGINX.

Run `python manage.py upgrade` for a controlled release upgrade. Do not run
migrations as part of a normal service restart.

Operational commands:

```bash
python manage.py status
python manage.py create_backup --company-code acme --login-id owner
```

The uninstall scripts require an explicit data-removal confirmation token.

## Windows

The Windows installer must provision Python 3.13, PostgreSQL, Redis, a signed
service wrapper, and Caddy (or an approved gateway). It then runs
`windows/register-services.ps1` elevated. The generated environment file is
stored under `C:\ProgramData\Mhami\config` rather than the application
directory and is restricted to `SYSTEM`, administrators, and the Mhami
service identities. The API, worker, and beat bind to loopback; only the
gateway is exposed to the network. Each Mhami service runs under its own
non-interactive virtual service account (`NT SERVICE\MhamiApi`,
`NT SERVICE\MhamiWorker`, or `NT SERVICE\MhamiBeat`) rather than
`LocalSystem`.

## Deployment modes

- **Central server:** configure a real DNS name, TLS, backups, monitoring, and
  a network policy allowing client devices to reach only the gateway.
- **Standalone company:** keep all services on one machine, bind databases and
  the API to loopback, and enable an explicit local-network firewall rule if
  other devices need access.

These files are an operational foundation, not yet a signed one-click
installer. Production support requires clean-install, upgrade, reboot, and
uninstall validation on every supported OS version.

## Bootstrapper

`installer.py` is the cross-platform preparation step used by a future GUI
installer. It generates independent secrets and writes an environment file
without overwriting an existing file unless `--force` is supplied:

```bash
python deploy/native/installer.py \
  --mode standalone \
  --env-file /etc/mhami/mhami.env \
  --data-root /var/lib/mhami
```

It does not silently install PostgreSQL, Redis, or a service wrapper. Those
dependencies must come from approved operating-system packages or the signed
installer bundle, then `manage.py upgrade` and service registration are run.
