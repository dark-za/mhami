# Windows native runtime

The Windows installer must provision PostgreSQL and Redis as separate local
services, then register the Mhami API, worker, beat, and optional connector as
Windows services. The application must run under dedicated non-admin virtual service accounts
(`NT SERVICE\MhamiApi`, `NT SERVICE\MhamiWorker`, and `NT SERVICE\MhamiBeat`)
and bind the API to loopback unless the setup explicitly configures a trusted
gateway. Secrets are stored in
`C:\ProgramData\Mhami\config\mhami.env`; the registration script removes
inherited ACLs and grants read access only to `SYSTEM`, administrators, and
the three Mhami service identities.

The installer should invoke the same commands used by Linux:

```powershell
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py doctor --strict
```

Service wrappers may use a signed NSSM package or a maintained native wrapper.
The wrapper choice is an installer concern and must not leak into Django
settings or application code.
