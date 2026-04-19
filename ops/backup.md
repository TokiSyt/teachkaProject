# Database Backup

## Render (production)

Render Basic tier runs **automatic daily backups** (7-day retention). View and download them:
Render dashboard → your PostgreSQL instance → Backups tab.

Before any risky deploy, also take a manual dump as extra safety:

```bash
pg_dump "$DATABASE_URL" --no-acl --no-owner -Fc -f backup_$(date +%Y%m%d_%H%M%S).dump
```

Store the `.dump` file somewhere safe (local machine, cloud storage). The file is compressed — a 100 MB DB produces ~10 MB dump.

## Local Docker stack

```bash
docker compose exec db pg_dump -U postgres -d teachkadb -Fc -f /tmp/backup.dump
docker compose cp db:/tmp/backup.dump ./backup_$(date +%Y%m%d).dump
```

## What to back up before a deploy

- DB dump (above)
- `mediafiles/` if you store user uploads (`docker compose cp web:/app/mediafiles ./mediafiles_backup`)
- Note the current git commit: `git rev-parse HEAD`
