# Database Backup

## Hetzner (production)

Postgres runs as the `db` container in the prod stack (`docker-compose.prod.yml`).
There is **no managed backup** — take dumps yourself. On the Hetzner host:

```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U postgres -d teachkadb -Fc -f /tmp/backup.dump
docker compose -f docker-compose.prod.yml cp db:/tmp/backup.dump \
  ./backup_$(date +%Y%m%d_%H%M%S).dump
```

Run it on a daily cron and ship the `.dump` off-box (e.g. `scp` / object storage).
The file is compressed — a 100 MB DB produces ~10 MB dump. Always dump before a risky deploy.

## Local Docker stack

```bash
docker compose exec db pg_dump -U postgres -d teachkadb -Fc -f /tmp/backup.dump
docker compose cp db:/tmp/backup.dump ./backup_$(date +%Y%m%d).dump
```

## What to back up before a deploy

- DB dump (above)
- `mediafiles/` if you store user uploads (`docker compose cp web:/app/mediafiles ./mediafiles_backup`)
- Note the current git commit: `git rev-parse HEAD`
