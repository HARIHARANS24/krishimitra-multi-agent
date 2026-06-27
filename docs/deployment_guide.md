# KrishiMitra AI — Deployment Guide

This guide covers three deployment paths: **Streamlit Community Cloud** (fastest for a demo/Kaggle submission), **Docker** (portable, runs anywhere), and **Google Cloud Run** (scalable, production-style).

The app runs in a fully functional **offline/simulated mode** without any API keys — all three paths work out of the box for demo purposes. Configure `GOOGLE_API_KEY` to enable live Gemini reasoning and translation.

---

## 0. Prerequisites

- Python 3.11+
- (Optional) A Gemini API key from [Google AI Studio](https://aistudio.google.com/) for live AI reasoning
- (Optional) Docker, for the Docker/Cloud Run paths
- (Optional) A Google Cloud project with billing enabled, for Cloud Run

---

## 1. Local development

```bash
git clone <your-repo-url> krishimitra-ai
cd krishimitra-ai
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env with real keys if available

python -m database.seed_data     # seed demo schemes + market data
streamlit run app.py
```

Visit `http://localhost:8501`.

---

## 2. Streamlit Community Cloud

1. Push this repository to GitHub (public or private with Streamlit Cloud access granted).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo, branch, and set the main file path to `app.py`.
4. Under **Advanced settings → Secrets**, paste your environment variables in TOML format, e.g.:
   ```toml
   GOOGLE_API_KEY = "your_real_key"
   SECRET_KEY = "a_long_random_string"
   RATE_LIMIT_PER_MINUTE = 30
   ```
   `config/settings.py` reads from `os.environ`, and Streamlit Cloud injects secrets as environment variables, so no code changes are needed.
5. Deploy. Streamlit Cloud auto-installs `requirements.txt` and auto-detects the `pages/` directory for the multi-page app.
6. **Database note:** Streamlit Cloud's filesystem is ephemeral across redeploys. For a persistent demo, either accept that the SQLite file resets on redeploy (fine for a capstone demo — `seed_data.py` re-seeds automatically via `db_manager.py`'s schema bootstrap), or point `DATABASE_PATH` at a mounted volume / external DB in a more permanent setup.

---

## 3. Docker (any host)

Build and run locally:

```bash
docker build -t krishimitra-ai .
docker run -p 8501:8501 \
  -e GOOGLE_API_KEY=your_real_key \
  -e SECRET_KEY=a_long_random_string \
  -v krishimitra_data:/app/database/data \
  krishimitra-ai
```

Visit `http://localhost:8501`.

To use `docker-compose` instead:

```bash
docker compose up --build
```

(see `docker-compose.yml` in the repo root.)

---

## 4. Google Cloud Run

Cloud Run runs the same container as above, scaled on demand.

```bash
# 1. Authenticate and set your project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build and push the container via Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/krishimitra-ai

# 3. Deploy to Cloud Run
gcloud run deploy krishimitra-ai \
  --image gcr.io/YOUR_PROJECT_ID/krishimitra-ai \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8501 \
  --set-env-vars GOOGLE_API_KEY=your_real_key,SECRET_KEY=a_long_random_string,RATE_LIMIT_PER_MINUTE=30
```

Notes:
- `--region asia-south1` (Mumbai) is a sensible default for low latency to Indian farmers; pick any supported region.
- Cloud Run containers have an **ephemeral filesystem** by default. For persistent farm/advisory data beyond a demo, mount a [Cloud Run volume backed by Cloud Storage FUSE](https://cloud.google.com/run/docs/configuring/services/storage) at the path configured in `DATABASE_PATH`, or migrate `database/db_manager.py` to a managed Postgres/Cloud SQL instance for production (the parameterized-query interface makes that a drop-in swap behind the same `DatabaseManager` API).
- Use **Secret Manager** instead of plain `--set-env-vars` for real API keys in production:
  ```bash
  gcloud secrets create gemini-api-key --data-file=-
  gcloud run deploy krishimitra-ai --update-secrets=GOOGLE_API_KEY=gemini-api-key:latest ...
  ```

---

## 5. Running the MCP servers independently

Each MCP server is a standalone, runnable module — useful for demoing MCP integration separately from the Streamlit app, or for connecting an external MCP-compatible agent host to KrishiMitra's tools:

```bash
python -m mcp_servers.weather_server
python -m mcp_servers.crop_db_server
python -m mcp_servers.knowledge_base_server
python -m mcp_servers.market_price_server
```

Each blocks on stdio, waiting for an MCP client (see `mcp_servers/mcp_client.py` for a working client example, and `tests/test_mcp.py` for live calls against all four servers).

---

## 6. Running tests before deploying

```bash
pip install -r requirements.txt
pytest tests/ -v
```

All 59 tests (security, agents, workflow, MCP) should pass without any API keys configured — the suite is designed to validate the offline/simulated code paths that graders or CI pipelines will exercise by default.

---

## 7. Production hardening checklist

- [ ] Set a strong, unique `SECRET_KEY` (not the placeholder).
- [ ] Configure real `GOOGLE_API_KEY` via a secrets manager, not plain env vars, in cloud deployments.
- [ ] Move `RATE_LIMIT_PER_MINUTE` enforcement to a shared store (e.g. Redis) if running multiple container replicas — the in-memory `SlidingWindowRateLimiter` is per-process.
- [ ] Migrate SQLite to Cloud SQL/Postgres if you need durability across redeploys or multi-instance writes.
- [ ] Put the app behind HTTPS (Streamlit Cloud and Cloud Run do this by default).
- [ ] Review `security/` module settings (`MAX_INPUT_LENGTH`, `ENABLE_PROMPT_INJECTION_GUARD`, `ENABLE_PII_FILTER`) for your risk tolerance.
