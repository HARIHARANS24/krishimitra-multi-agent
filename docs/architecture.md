# KrishiMitra AI — Architecture

## 1. Agent Interaction Flow

The Coordinator Agent is the single entry point for every farmer query. It validates and secures input, classifies intent, dispatches to one or more specialist agents, reflects on their combined output, and aggregates a final explainable answer.

```mermaid
flowchart TD
    U[Farmer<br/>Streamlit UI] -->|free-text query + farm context| SEC[Security Layer<br/>rate limit · validate · injection guard]
    SEC --> COORD[Coordinator Agent]

    COORD -->|classify intent| ROUTE{Intent Router<br/>keyword + Gemini fallback}

    ROUTE -->|weather| WA[Weather Agent]
    ROUTE -->|crop| CA[Crop Recommendation Agent]
    ROUTE -->|pest| PA[Pest & Disease Agent]
    ROUTE -->|fertilizer| FA[Fertilizer Agent]
    ROUTE -->|market| MA[Market Intelligence Agent]
    ROUTE -->|scheme| SA[Government Scheme Agent]
    ROUTE -->|planning| PLA[Planning Agent]

    WA -->|AgentResponse| AGG[Aggregator]
    CA -->|AgentResponse| AGG
    PA -->|AgentResponse| AGG
    FA -->|AgentResponse| AGG
    MA -->|AgentResponse| AGG
    SA -->|AgentResponse| AGG
    PLA -->|AgentResponse| AGG

    AGG --> REFLECT[Reflection Pass<br/>confidence check · agreement check]
    REFLECT --> LOG[(advisory_logs<br/>SQLite)]
    REFLECT --> OUT[Final Explainable Answer<br/>+ confidence + alternatives]
    OUT --> U

    WA -.uses.-> WT[tools/weather_tool.py]
    CA -.uses.-> CT[tools/crop_tool.py]
    PA -.uses.-> PT[tools/pest_tool.py]
    FA -.uses.-> FT[tools/fertilizer_tool.py]
    MA -.uses.-> MT[tools/market_tool.py]
    SA -.uses.-> ST[tools/scheme_tool.py]
```

## 2. MCP Architecture

Each domain's tool logic is exposed twice: in-process (fast path used by default) and over MCP stdio servers (protocol-compliant path used for interoperability with other MCP hosts, and exercised directly in `tests/test_mcp.py`).

```mermaid
flowchart LR
    subgraph Agents["KrishiMitra Agents"]
        WA2[Weather Agent]
        CA2[Crop Agent]
        PDA[Pest/Fertilizer/Scheme Agents]
        MA2[Market Agent]
    end

    subgraph MCPClient["mcp_servers/mcp_client.py"]
        SESSION[ClientSession<br/>stdio transport]
    end

    subgraph Servers["MCP Servers (independently runnable)"]
        WS[weather_server.py<br/>get_current_weather<br/>get_irrigation_recommendation]
        CS[crop_db_server.py<br/>recommend_crops<br/>list_known_crops]
        KS[knowledge_base_server.py<br/>get_pest_disease_risk<br/>get_fertilizer_plan<br/>search_government_schemes]
        MS[market_price_server.py<br/>get_market_price<br/>compare_crop_profitability<br/>record_market_price]
    end

    Agents -.in-process call.-> Tools[tools/*.py]
    Agents -."MCP protocol call (optional)".-> SESSION
    SESSION -->|spawn subprocess + JSON-RPC| WS
    SESSION -->|spawn subprocess + JSON-RPC| CS
    SESSION -->|spawn subprocess + JSON-RPC| KS
    SESSION -->|spawn subprocess + JSON-RPC| MS

    WS --> Tools
    CS --> Tools
    KS --> Tools
    MS --> Tools
    Tools --> DB[(SQLite<br/>krishimitra.db)]
```

## 3. Deployment Architecture

```mermaid
flowchart TB
    subgraph Client
        Browser[Farmer's Browser / Mobile]
    end

    subgraph Deploy["Deployment Targets (pick one)"]
        SC[Streamlit Community Cloud]
        CR[Google Cloud Run<br/>container]
        DK[Docker container<br/>any host]
    end

    subgraph App["KrishiMitra Container/Process"]
        ST[Streamlit App<br/>app.py + pages/]
        AG[Agents + Coordinator]
        SECM[Security Module]
        DBL[(SQLite volume)]
    end

    subgraph External["External Services (optional)"]
        GEMINI[Gemini API]
        WEATHERAPI[Open-Meteo API]
    end

    Browser --> SC
    Browser --> CR
    Browser --> DK
    SC --> ST
    CR --> ST
    DK --> ST
    ST --> AG
    AG --> SECM
    AG --> DBL
    AG -.optional, if key configured.-> GEMINI
    AG -.optional, falls back to simulated weather.-> WEATHERAPI
```

## 4. Data Model

See `database/schema.sql` for the full SQLite DDL. Summary:

| Table | Purpose |
|---|---|
| `users` | Farmer accounts (phone stored as a hash, never plaintext) |
| `farm_profiles` | One or more plots per farmer: region, soil, area, irrigation source |
| `crop_history` | What was grown, when, and yield outcome |
| `weather_logs` | Cached/observed weather readings per region |
| `advisory_logs` | Every recommendation + reasoning, for audit & explainability |
| `market_data` | Crop price snapshots per market/region |
| `government_schemes` | Curated scheme reference data |

## 5. Explainability Contract

Every agent returns an `AgentResponse` (see `agents/base_agent.py`) with four mandatory fields: `recommendation`, `confidence_score` (0–100), `factors_considered`, and `alternatives`. This is enforced by the dataclass itself, not left to convention — the Coordinator's aggregation step can rely on every specialist response having this shape.
