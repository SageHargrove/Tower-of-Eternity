# World/Arena server — the piece you actually host for multiplayer.
# (The repo-root Dockerfile containerizes the main single-player game
# backend instead; you likely don't need that one for hosting.)
#
# Build (from the repo root):
#   docker build -t tower-world-server ./arena_server
#
# Run (persists arena.db in a named volume, admin actions enabled):
#   docker run -d --name world-server -p 8001:8001 \
#     -e ARENA_ADMIN_KEY=change-me-to-something-long \
#     -v world_data:/app/data \
#     tower-world-server
#
# Then point DEFAULT_ARENA_SERVER_URL (frontend/src/api/arenaServerClient.js)
# at http://<your-host>:8001 and rebuild the frontend.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# arena.db lives in /app/data so a volume mount survives image rebuilds.
ENV ARENA_DB_PATH=/app/data/arena.db
RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
