# Incident Runbook

## Site is down / returning 5xx

**1. Check logs**

Render dashboard → your service → Logs tab.

Locally:
```bash
make logs
# or
docker compose logs -f web
```

**2. Check health endpoint**

```bash
curl https://teachka.com/healthz/
# Healthy:  {"status": "ok", "db": true}
# DB down:  {"status": "error", "db": false}  → HTTP 503
```

**3. DB is down**

- If DB is unreachable, restart the DB instance from the Render dashboard.
- If data loss is suspected, restore from latest dump (see `restore.md`).

**4. Restart the web service**

Render dashboard → Manual Deploy → "Clear build cache & deploy" if code is fine but container is wedged.

Locally:
```bash
make restart
```

**5. Rollback to last known good commit**

```bash
git log --oneline -10          # find the good commit hash
git checkout <hash>
git push origin HEAD:main --force-with-lease   # only if truly needed
```

Then trigger a new Render deploy.

---

## High error rate but site is up

- Check `django.request` logs for repeated tracebacks.
- Check if a recent migration broke something: `make shell` → poke affected models.
- If caused by a bad deploy, rollback (see above).

---

## Forgot SECRET_KEY / env var missing

Symptom: `ValueError: SECRET_KEY environment variable is required when DEBUG=False`

Fix: Render dashboard → Environment → add the missing var → redeploy.

---

## Contacts

| Role | Contact |
|------|---------|
| Owner | Tiago Silva |
