# 🌾 KrishiMitra AI — Multi-Agent Farmer Advisory System

> **Kaggle AI Agents: Intensive Vibe Coding Capstone Project**

KrishiMitra AI ("Friend of Agriculture") is a multi-agent advisory platform that helps small and medium Indian farmers make better day-to-day decisions: what to grow, when to irrigate, how to manage pests, how much fertilizer to apply, when to sell, which government schemes apply to them, and how to plan their season — all explained in plain language, in their own language.

It is built as a **coordinator + 7 specialist agents** system, backed by **4 independent MCP servers**, a dedicated **security module**, a **SQLite** data layer, and a **6-page Streamlit app** with English/Tamil/Hindi support.

The whole system runs end-to-end **without any API keys** (offline/simulated mode using rule-based agronomic logic), and automatically upgrades to live Gemini-powered reasoning and live weather data when `GOOGLE_API_KEY` is configured — so it is fully demoable by anyone who clones the repo.

---

## ✨ Features

| # | Feature | Where |
|---|---|---|
| 1 | Crop recommendations (Top-3, with suitability scoring) | `agents/crop_agent.py` |
| 2 | Weather-based farming advice & irrigation prediction | `agents/weather_agent.py` |
| 3 | Pest & disease risk guidance | `agents/pest_agent.py` |
| 4 | Fertilizer (NPK) recommendations by growth stage | `agents/fertilizer_agent.py` |
| 5 | Irrigation scheduling | `tools/weather_tool.py::estimate_irrigation_need` |
| 6 | Market price insights & profit opportunity scoring | `agents/market_agent.py` |
| 7 | Farming calendar planning (weekly/monthly/seasonal) | `agents/planning_agent.py` |
| 8 | Government scheme search & eligibility explanation | `agents/scheme_agent.py` |
| 9 | Regional language support (English, Tamil, Hindi) | `tools/translation_tool.py`, `frontend/i18n/` |
| 10 | Explainable recommendations (reason, confidence, alternatives) | `agents/base_agent.py::AgentResponse` |

---

## 🧠 Architecture

KrishiMitra demonstrates **5 of the 6** Kaggle capstone focus areas:

1. ✅ **Multi-Agent System** — a Coordinator Agent routes to 7 specialist agents, aggregates their responses, and performs a reflection pass (`agents/coordinator_agent.py`).
2. ✅ **MCP Server Integration** — 4 independently runnable MCP servers (weather, crop DB, knowledge base, market price) plus a working stdio client, exercised by real protocol calls in `tests/test_mcp.py`.
3. ✅ **Agent Skills** — each agent has a tightly scoped `description` + `tools` allow-list (least-privilege), defined in `agents/base_agent.py` and mirrored into the ADK-style spec in `agents/adk_integration.py`.
4. ✅ **Security Features** — a dedicated `security/` package: input validation, rate limiting, prompt-injection guarding, PII redaction, secrets management, secure file handling.
5. ✅ **Deployability** — Dockerfile, docker-compose, and guides for Streamlit Cloud and Google Cloud Run (`docs/deployment_guide.md`).

See **[`docs/architecture.md`](docs/architecture.md)** for full Mermaid diagrams of the agent interaction flow, MCP architecture, and deployment architecture.

### Agent roster

| Agent | Responsibility |
|---|---|
| **Coordinator** | Understands the query, routes tasks, aggregates + reflects, logs to DB |
| **Weather** | Fetches forecast, analyzes rainfall, predicts irrigation need, raises warnings |
| **Crop Recommendation** | Scores crops by soil/season/rainfall fit + local demand |
| **Pest & Disease** | Assesses risk from current weather, explains symptoms/prevention/treatment |
| **Fertilizer** | NPK dosage by crop, soil type, and growth stage |
| **Market Intelligence** | Price trend + profit opportunity scoring, crop comparison |
| **Government Scheme** | Searches schemes, explains eligibility against the farmer's profile |
| **Planning** | Generates weekly/monthly calendars sequencing sowing → flowering → harvest |

### AI integration

- **Structured outputs** — `BaseAgent.reason_with_gemini()` requests JSON-only responses from Gemini, with a deterministic offline fallback.
- **Tool/function calling** — demonstrated both via in-process tool functions and real MCP `@mcp.tool()` definitions.
- **Planning & multi-step reasoning** — `PlanningAgent` sequences multi-stage farming calendars; `CoordinatorAgent` performs multi-agent dispatch + aggregation.
- **Reflection** — `CoordinatorAgent._reflect()` checks confidence levels and inter-agent agreement before finalizing an answer.
- **Agent collaboration** — the Coordinator combines independent specialist outputs into one explainable answer.

### Explainability example

```
[Crop Recommendation Agent]
Recommendation: Groundnut (suitability score 87.3/100, ~110 day crop cycle, needs ~25 mm water/week).

Reason:
  - Conditions evaluated for region: Tirunelveli.
  - Soil compatibility for Groundnut with 'red' soil: 100%.
  - Season compatibility for 'kharif' season: 100%.
  - Rainfall compatibility at 850 mm: 92%.
  - Local market demand index: 78%.

Confidence: 87%

Alternatives:
  - Millet
  - Maize
```

---

## 🗂️ Project Structure

```
krishimitra-ai/
├── agents/                 # Coordinator + 7 specialist agents, ADK integration shim
├── tools/                  # Domain logic (weather, crop, pest, fertilizer, market, scheme, translation)
├── mcp_servers/            # 4 MCP servers + shared stdio client
├── database/               # SQLite schema, manager, seed data
├── security/                # Input validation, rate limiting, prompt-injection guard, PII filter, secrets, file handling
├── config/                 # Centralized settings loader
├── frontend/
│   ├── i18n/                # en.json, ta.json, hi.json
│   └── components/          # Shared Streamlit UI helpers
├── pages/                  # Streamlit multi-page app pages
├── tests/                  # pytest suite (security, agents, workflow, MCP)
├── docs/                   # Architecture diagrams, deployment guide, writeup, video script
├── app.py                  # Streamlit entry point (Dashboard)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

```bash
git clone <your-repo-url> krishimitra-ai
cd krishimitra-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # optionally add a real GOOGLE_API_KEY
python -m database.seed_data    # seed demo schemes + market data

streamlit run app.py
```

Open `http://localhost:8501`. The app works immediately in offline/simulated mode.

### Run the test suite

```bash
pytest tests/ -v
```

59 tests across security, individual agents, the full coordinator workflow, and live MCP protocol calls — all pass without any API keys configured.

### Run an MCP server standalone

```bash
python -m mcp_servers.weather_server
```

---

## 🔐 Security

See [`security/`](security/) and the "Security Requirements" section of the original spec — implemented as:

- **API key management** via `.env` + `config/settings.py` (never hard-coded; `security/secrets_manager.py` masks any secret before it could appear in a log).
- **Input validation** (`security/input_validation.py`): length limits, character allow-listing, numeric range checks, enum validation for soil/season.
- **Rate limiting** (`security/rate_limiter.py`): per-identity sliding window, enforced at the Coordinator entry point.
- **Prompt injection protection** (`security/prompt_injection_guard.py`): pattern-based detection + data-tag wrapping so farmer text is never treated as instructions by the LLM.
- **Sensitive data filtering** (`security/data_filter.py`): regex-based PII redaction (phone, email, Aadhaar-like, GPS) before anything reaches an LLM prompt or a log line.
- **Secure file handling** (`security/secure_file_handling.py`): extension allow-listing, size limits, randomized storage filenames, path-traversal guards.

---

## 🌍 Deployment

Full instructions in [`docs/deployment_guide.md`](docs/deployment_guide.md) for:

1. **Streamlit Community Cloud**
2. **Docker** / `docker-compose`
3. **Google Cloud Run**

---

## 📸 Screenshots

> _Add screenshots here before submission:_
> - `docs/screenshots/dashboard.png`
> - `docs/screenshots/advisory_assistant.png`
> - `docs/screenshots/crop_planner.png`
> - `docs/screenshots/market_insights.png`
> - `docs/screenshots/government_schemes.png`

---

## 🛣️ Future Improvements

- Voice input/output for low-literacy farmers (Tamil/Hindi speech-to-text and text-to-speech).
- Satellite/drone imagery integration for crop health monitoring (a natural extension of the Pest & Disease Agent).
- Hyperlocal weather via on-ground IoT sensors instead of regional forecast averages.
- Mandi price ingestion pipeline from data.gov.in's live APIs (currently demoed with seeded/simulated data).
- A real-time notification channel (SMS/WhatsApp) for weather warnings and scheme deadlines.
- Migrating the rate limiter and SQLite layer to Redis/Cloud SQL for true multi-instance production scale.
- Expanding the crop/pest/fertilizer knowledge bases beyond the curated demo set, ideally sourced from ICAR/state agriculture department datasets.

---

## 📄 License

This is a capstone/demo project built for the Kaggle AI Agents: Intensive Vibe Coding Capstone. Adapt freely for educational and non-commercial use; verify agronomic and scheme guidance with certified local authorities before real-world deployment.
