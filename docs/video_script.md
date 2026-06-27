# KrishiMitra AI — 5-Minute Video Demonstration Script

**Total runtime target: 5:00** | Recommended: screen recording of the live Streamlit app + occasional architecture diagram overlays.

---

## 1. Problem (0:00 – 0:50)

**[On screen: a split image — a farmer in a field, and a cluttered phone screen with 5 different apps]**

> "Meet a small farmer in Tamil Nadu with three acres of land. Before sowing, she needs to answer five questions: What should I grow? Will it rain? What pests should I watch for? How much fertilizer do I need? And is there a government scheme that helps me?
>
> Today, those five answers live in five different places — a weather app, a WhatsApp forward from a neighbor, a fertilizer shop's guess, and a government PDF she's never seen. None of them explain *why*, and none of them talk to each other.
>
> KrishiMitra AI puts all five behind one conversation — in her own language — and every single answer comes with its reasoning attached."

---

## 2. Why Agents (0:50 – 1:40)

**[On screen: docs/architecture.md's agent interaction flow diagram]**

> "We could have asked one large language model to 'give farming advice' in a single prompt. We didn't, for one reason: trust.
>
> A farmer's input budget is real money. So instead of one black box, KrishiMitra has seven specialist agents — Weather, Crop Recommendation, Pest and Disease, Fertilizer, Market Intelligence, Government Scheme, and Planning — each backed by an inspectable scoring function, not an LLM guess.
>
> A Coordinator Agent sits on top. It classifies the farmer's question, routes it to the right specialists, and — this is the part I'm proud of — it *reflects*. If one agent's confidence is low, or two agents disagree, the Coordinator says so honestly instead of papering over it."

---

## 3. Architecture (1:40 – 2:40)

**[On screen: MCP architecture diagram, then deployment architecture diagram]**

> "Under the hood: every agent's domain logic — weather, crop scoring, pest risk, fertilizer dosage, market trends, scheme search — is exposed two ways. In-process, for speed inside the app. And over four real MCP servers, using the standard stdio protocol, so any other MCP-compatible agent host could plug into KrishiMitra's knowledge without touching our code.
>
> Security isn't an afterthought here — it's a dedicated module sitting between every farmer message and every agent: rate limiting, input validation, a prompt-injection guard that wraps farmer text in data tags the model is told never to treat as instructions, and PII redaction before anything reaches an external API.
>
> Everything's backed by SQLite with parameterized queries, and ships with a Dockerfile, docker-compose, and deployment guides for Streamlit Cloud, Docker, and Google Cloud Run."

---

## 4. Demo (2:40 – 4:10)

**[Screen recording: live app]**

> "Let's see it live."

**(0:00–0:25 of this segment) Dashboard:**
> "The Dashboard shows current weather and a top crop recommendation immediately — no typing required. Here, for red soil in Tirunelveli during kharif season, it's recommending Groundnut with an 87% confidence score, and I can expand to see exactly why."

**(0:25–1:00) Advisory Assistant:**
> "Now the chat. I'll ask: 'Will rain affect my crop and how much fertilizer should I use?' Watch — it routes to both the Weather Agent and the Fertilizer Agent, and combines them into one answer. Forecast rainfall, irrigation deficit, NPK dosage by growth stage — all in one response, all explained."

**(1:00–1:20) Crop Planner:**
> "In Crop Planner, I pick the recommended crop and generate a full farming calendar — sowing, flowering top-dressing, pod-filling irrigation checkpoint, expected harvest date — broken into weekly and monthly views."

**(1:20–1:40) Market Insights:**
> "Market Insights shows price trends and a profit opportunity score, comparing Groundnut against Cotton and Millet with an actual price history chart."

**(1:40–1:30) Government Schemes & language switch:**
> "Government Schemes lets her search by keyword — 'insurance' — and see eligibility explained against her own farm profile. And switching the language selector to Tamil translates the entire interface instantly."

---

## 5. Technical Implementation (4:10 – 4:40)

**[On screen: project file tree / VS Code]**

> "Everything you saw is backed by real, tested code: 59 automated tests covering the security module, every individual agent, the full coordinator workflow including a simulated prompt-injection attempt, and live calls against all four MCP servers — all passing without a single API key configured, because the whole system has a deterministic offline fallback. Configure a Gemini key, and intent classification, translation, and reasoning upgrade to live AI calls automatically."

---

## 6. Future Roadmap (4:40 – 5:00)

**[On screen: bullet list overlay]**

> "Next: voice input for low-literacy farmers, satellite imagery for visual pest diagnosis, live mandi price feeds, and WhatsApp alerts for weather warnings and scheme deadlines.
>
> KrishiMitra AI: one conversation, seven specialist agents, every answer explained. Thank you."

**[End card: project title, GitHub link, "Built for Kaggle AI Agents: Intensive Vibe Coding Capstone"]**
