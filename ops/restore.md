# Database Restore

## Restore to local Docker stack

```bash
# Copy dump into container
docker compose cp ./backup.dump db:/tmp/backup.dump

# Drop and recreate DB (WARNING: destroys all current data)
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS teachkadb;"
docker compose exec db psql -U postgres -c "CREATE DATABASE teachkadb;"

# Restore
docker compose exec db pg_restore -U postgres -d teachkadb /tmp/backup.dump

# Re-run migrations in case schema diverged
docker compose exec web python manage.py migrate
```

## Restore to Render (production)

**From automatic backup (easiest):**
Render dashboard → your PostgreSQL instance → Backups tab → select point-in-time → Restore.

**From a manual dump:**
1. Get the Render external DB URL from the dashboard.
2. From a machine with `pg_restore` installed:

```bash
pg_restore --no-acl --no-owner -d "$DATABASE_URL" backup.dump
```

3. Redeploy the app so `entrypoint.sh` runs `migrate`.

## Verify after restore

```bash
# Spot-check row counts
docker compose exec db psql -U postgres -d teachkadb -c "\dt"
docker compose exec db psql -U postgres -d teachkadb -c "SELECT COUNT(*) FROM users_customuser;"
```
