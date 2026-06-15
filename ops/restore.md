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

## Restore to Hetzner (production)

On the Hetzner host, with the prod stack running:

```bash
# Copy dump into the db container
docker compose -f docker-compose.prod.yml cp ./backup.dump db:/tmp/backup.dump

# Drop and recreate DB (WARNING: destroys all current data)
docker compose -f docker-compose.prod.yml exec db psql -U postgres -c "DROP DATABASE IF EXISTS teachkadb;"
docker compose -f docker-compose.prod.yml exec db psql -U postgres -c "CREATE DATABASE teachkadb;"

# Restore
docker compose -f docker-compose.prod.yml exec db pg_restore -U postgres -d teachkadb /tmp/backup.dump

# Re-run migrations in case schema diverged
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## Verify after restore

```bash
# Spot-check row counts
docker compose exec db psql -U postgres -d teachkadb -c "\dt"
docker compose exec db psql -U postgres -d teachkadb -c "SELECT COUNT(*) FROM users_customuser;"
```
