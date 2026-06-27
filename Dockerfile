# ============================================================
# KrishiMitra AI - Dockerfile
# ============================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

# System deps kept minimal: SQLite is built into Python's stdlib.
# curl is included only for the container HEALTHCHECK below.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persisted SQLite location (mount a volume here in production).
RUN mkdir -p /app/database/data
ENV DATABASE_PATH=/app/database/data/krishimitra.db

# Seed demo data at build time so the image is immediately demoable.
RUN python -m database.seed_data || true

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]
