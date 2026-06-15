# Incident Runbook

## Site is down / returning 5xx

**1. Check logs**

On the Hetzner host:
```bash
docker compose -f docker-compose.prod.yml logs -f web
```

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

- If DB is unreachable, restart it: `docker compose -f docker-compose.prod.yml restart db`.
- If data loss is suspected, restore from latest dump (see `restore.md`).

**4. Restart the web service**

On the Hetzner host, if code is fine but the container is wedged:
```bash
docker compose -f docker-compose.prod.yml restart web
# or rebuild + recreate after a code change
docker compose -f docker-compose.prod.yml up -d --build web
```

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

Then redeploy on the Hetzner host: `git pull && docker compose -f docker-compose.prod.yml up -d --build`.

---

## High error rate but site is up

- Check `django.request` logs for repeated tracebacks.
- Check if a recent migration broke something: `make shell` → poke affected models.
- If caused by a bad deploy, rollback (see above).

---

## Forgot SECRET_KEY / env var missing

Symptom: `ValueError: SECRET_KEY environment variable is required when DEBUG=False`

Fix: add the missing var to `.env` on the Hetzner host, then `docker compose -f docker-compose.prod.yml up -d`.

---

## Contacts

| Role | Contact |
|------|---------|
| Owner | Tiago Silva |
