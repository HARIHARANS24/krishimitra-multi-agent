# KrishiMitra AI — Kaggle Capstone Writeup

## Problem Statement

India has over 140 million farm holdings, the majority small or marginal (under 2 hectares). These farmers make high-stakes seasonal decisions — what to plant, how much fertilizer to buy, when to irrigate, when to sell — with fragmented information: weather forecasts in one app, mandi prices on a government portal, pest advice from a neighbor, scheme eligibility buried in PDFs on a different portal entirely. Each piece of advice typically arrives without explanation, making it hard for a farmer to judge whether to trust it, and harder still for an agricultural extension worker to scale personalized guidance across thousands of farmers.

KrishiMitra AI addresses this by unifying eight categories of agricultural decision support — crop selection, weather/irrigation, pest and disease risk, fertilizer dosage, market intelligence, scheme eligibility, seasonal planning, and regional-language access — behind one conversational interface, with every recommendation accompanied by its reasoning, a confidence score, and named alternatives.

## Why a Multi-Agent Architecture

A single monolithic LLM prompt asked to "give farming advice" tends to produce generic, unverifiable text. Decomposing the problem into specialist agents has three concrete benefits realized in this project:

1. **Separation of concerns with auditable logic.** The Crop Recommendation Agent's scoring (soil match × season match × rainfall fit × demand index) is a deterministic, inspectable function (`tools/crop_tool.py`) — not a black box the LLM invents per call. The same applies to fertilizer dosage and pest risk. This makes the system's advice *checkable* by an agronomist, which matters when the stakes are a farmer's input costs.
2. **Independent failure domains.** If the Market Intelligence Agent has no price data for an obscure crop, it degrades to a neutral score and a clear note — it does not block the Weather or Crop agents from answering. The Coordinator's dispatch loop (`agents/coordinator_agent.py::handle_query`) wraps each specialist call so one agent's exception never breaks the whole response.
3. **Composable reasoning.** The Planning Agent reuses the Fertilizer Agent's dosage logic to place fertilizer milestones on a calendar; the Coordinator reuses every specialist's `AgentResponse` contract to build one coherent answer regardless of which subset of agents fired. This is multi-agent collaboration in the literal sense — agents calling into each other's domain logic, not just parallel independent calls.

## Architecture Overview

**Coordinator Agent** is the single entry point. For every farmer query it: (1) enforces a sliding-window rate limit per session, (2) validates and sanitizes the input, (3) classifies intent via keyword matching with a Gemini-backed fallback for ambiguous phrasing, (4) dispatches to the relevant specialist agent(s), (5) runs a reflection pass that flags low-confidence or highly divergent specialist outputs rather than silently averaging them away, and (6) persists the full interaction — query, recommendation, confidence, and reasoning — to a SQLite `advisory_logs` table for auditability.

**Seven specialist agents** — Weather, Crop Recommendation, Pest & Disease, Fertilizer, Market Intelligence, Government Scheme, and Planning — each inherit from a shared `BaseAgent` that enforces a single explainability contract (`AgentResponse`: recommendation, confidence score, factors considered, alternatives) and centralizes security-aware LLM access (`reason_with_gemini`, which wraps farmer text in injection-guarded data tags and redacts PII before any prompt is sent to Gemini, and gracefully falls back to deterministic logic if no API key is configured).

**Four MCP servers** — weather, crop database, agricultural knowledge base (pest + fertilizer + schemes), and market price — expose the same domain tools over the Model Context Protocol's stdio transport, independently runnable (`python -m mcp_servers.weather_server`) and independently testable. A shared async client (`mcp_servers/mcp_client.py`) spawns each server as a subprocess, performs MCP `initialize`, lists available tools, and calls them — exercised directly by eight integration tests that prove real protocol round-trips, not mocked stubs.

**A dedicated security module** sits in front of every farmer interaction: input validation (length limits, character allow-listing, numeric range checks), a sliding-window rate limiter, a prompt-injection scanner that wraps untrusted text in delimited data tags so the LLM is instructed never to treat it as commands, a PII redaction layer (phone numbers, emails, Aadhaar-like numbers, GPS coordinates) applied before any text reaches an LLM prompt or a log line, a secrets manager that masks credentials in any diagnostic output, and a secure file-handling module (extension allow-listing, size caps, randomized storage filenames, path-traversal guards) for future document upload features.

**SQLite** backs seven tables (`users`, `farm_profiles`, `crop_history`, `weather_logs`, `advisory_logs`, `market_data`, `government_schemes`) accessed exclusively through parameterized queries in `database/db_manager.py` — no string-interpolated SQL anywhere in the codebase, even though input is already sanitized upstream (defense in depth).

**A six-page Streamlit application** (Dashboard, Advisory Assistant, Crop Planner, Market Insights, Government Schemes, Settings) provides the farmer-facing surface, with English/Tamil/Hindi support: static UI strings are translated via JSON dictionaries for instant, free rendering, while dynamic agent-generated recommendation text is translated through Gemini when configured, falling back to a curated phrase-substitution table otherwise — so language support degrades gracefully rather than failing outright in offline mode.

## AI Features Demonstrated

- **Structured outputs:** `BaseAgent.reason_with_gemini()` instructs Gemini to return JSON-only, parses defensively (stripping markdown fences if the model adds them anyway), and falls back to a deterministic dictionary if parsing or the API call fails.
- **Function/tool calling:** every domain operation (weather lookup, crop scoring, pest assessment, fertilizer dosage, market analysis, scheme search) is implemented as a typed Python function, exposed identically through direct agent calls and through `@mcp.tool()` definitions in the MCP servers.
- **Planning:** the Planning Agent sequences a crop's lifecycle into basal/flowering/pod-filling fertilizer milestones and builds week-by-week and month-by-month calendars from a single crop-duration parameter.
- **Reflection:** the Coordinator's `_reflect()` method explicitly checks for low-confidence specialist responses and high confidence-spread across agents, surfacing an honest caveat to the farmer rather than presenting a falsely unified answer.
- **Multi-step reasoning and agent collaboration:** a single query like "Will rain affect my crop and how much fertilizer should I use?" is decomposed into Weather + Fertilizer agent calls, each independently reasoned, then aggregated into one response with combined confidence.

## MCP Usage

MCP was used as more than a checkbox: the four servers are genuinely independent processes communicating over the standard stdio JSON-RPC transport, started on demand by the test suite and by any external MCP-compatible host that wants to integrate with KrishiMitra's domain knowledge (for example, a separate ADK agent or a different LLM application entirely). The registration table in `mcp_servers/mcp_client.py::MCP_SERVER_REGISTRY` demonstrates how a host would discover and spawn each server by name, and `tests/test_mcp.py` proves tool discovery (`list_tools`) and tool invocation (`call_tool`) work end-to-end for all four servers.

## Security Decisions, Explained

Security was treated as cross-cutting, not bolted on per-agent. The Coordinator is the single choke point where rate limiting and input validation are enforced, so no specialist agent needs to re-implement these checks, and no code path can bypass them by calling a specialist directly from the UI without going through `handle_query`. Prompt injection is addressed at two layers: a pattern-based scanner flags suspicious phrasing for audit logging, and — regardless of whether a known pattern matched — all farmer text is wrapped in `<farmer_input>` delimiter tags with an explicit system instruction telling Gemini never to follow instructions found inside them, which is more robust than pattern-matching alone against novel injection phrasings. PII redaction runs before text reaches any LLM prompt, not just before logging, because the prompt is the more consequential exposure surface (the LLM provider, not just our own logs). Secrets are never read anywhere except through `config/settings.py` and masked via `security/secrets_manager.py` if they ever need to appear in diagnostic output.

## Deployability

The project ships a multi-stage-ready `Dockerfile`, a `docker-compose.yml` for one-command local container runs, and a deployment guide covering Streamlit Community Cloud, Docker, and Google Cloud Run, including notes on persistent storage tradeoffs (SQLite's ephemeral-filesystem limitation on Cloud Run and Streamlit Cloud, with a clear upgrade path to Cloud SQL behind the same `DatabaseManager` interface) and secrets handling via Cloud Secret Manager for production deployments.

## Results

The full test suite — 59 tests spanning the security module, every individual specialist agent, the end-to-end coordinator workflow (including a simulated prompt-injection attempt and rate-limit exhaustion), and live MCP protocol round-trips against all four servers — passes deterministically with zero external API keys configured, confirming the system is fully functional in offline/simulated mode. The Streamlit app starts cleanly and serves all six pages; manual smoke testing confirmed the Dashboard, Advisory Assistant chat flow, Crop Planner calendar generation, and Market Insights price charting all render correctly against seeded demo data.

## Future Work

Priority next steps are voice input/output for low-literacy farmers, satellite/drone imagery integration extending the Pest & Disease Agent toward visual diagnosis, ingestion of live mandi price feeds from data.gov.in to replace the seeded demo dataset, SMS/WhatsApp notification channels for weather warnings and scheme deadlines, and migrating the rate limiter and database layer to Redis and Cloud SQL respectively to support true multi-instance production scale beyond the current single-process design.

---

*Word count: ~1,550 (well under the 2,500-word limit).*
