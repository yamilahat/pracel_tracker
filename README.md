# Smart Parcel Tracker

Self-hosted, privacy-aware parcel tracking assistant.

This repository is currently at Milestone 0: local backend foundation only.

## Local Development

Copy the example environment file:

```bash
cp .env.example .env
```

Start the local stack:

```bash
docker compose up --build
```

Run migrations:

```bash
docker compose exec api alembic upgrade head
```

Check the API:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Local Checks

```bash
pytest
ruff check .
ruff format --check .
```

