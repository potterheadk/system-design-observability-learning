# 🤖 Phase 4: The AI Site Reliability Engineer (SRE)

**Status:** Completed  
**Focus:** AI Agents, Tool Use, and Automated Incident Analysis  
**Tech Stack:** Python (FastAPI), Google Gemini (or Ollama), Strategy Pattern

## 📖 The Problem: "Data Rich, Insight Poor"
By Phase 3, our system generated massive amounts of data:
*   **Prometheus:** Thousands of data points.
*   **Logs:** JSON streams.
*   **Health API:** Status codes (`DEGRADED`, `DOWN`).

However, during an outage, a human engineer still had to:
1.  Look at the dashboard.
2.  Correlate the error rate.
3.  Judge if "13% errors" is bad or acceptable.

**The Goal:** Build an AI Agent that acts as a "Tier 1 Analyst." We can ask it, *"Why is the system failing?"* and it will query the live system, analyze the data, and write a summary.

---
## Before starting project in root folder (side by side with docker-compose file ) setup an .env with gemin
```
GEMINI_API_KEY=your-api-key
```
---

## 🏗️ Architecture: The Agentic Workflow

We didn't just "chat with PDF." We built an agent with **Tool Use**.

```ascii
User Question
("Why is service-b slow?")
       │
       ▼
┌────────────────────┐
│      AI Agent      │ 🧠 The "Brain"
│ (FastAPI + LLM)    │
└────────┬───────────┘
         │ 1. "I need facts before I answer."
         │    (Calls Function: fetch_system_health)
         ▼
┌────────────────────┐
│  Observability API │ 🔍 The "Tool" (Built in Phase 2)
└────────┬───────────┘
         │ 2. Returns JSON: { status: "DEGRADED", errorRate: 13.2% }
         ▼
    [Prometheus]
```

---

## 🛠️ Key Engineering Patterns

### 1. The Strategy Pattern (Model Agnostic)
We designed the system to be vendor-neutral. We can switch between **Google Gemini** (Cloud) and **Ollama** (Local) using a simple environment variable.

**Code Snippet (`llm_client.py`):**
```python
class LLMInterface:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class GeminiClient(LLMInterface):
    # Uses Google's API
    pass

class OllamaClient(LLMInterface):
    # Uses local Llama-3 model
    pass

def get_llm_client():
    if os.getenv("LLM_PROVIDER") == "ollama":
        return OllamaClient()
    return GeminiClient()
```

### 2. Tool Use (Grounding)
Large Language Models (LLMs) hallucinate. To prevent this, we **Ground** the AI in real-time data.
*   **Wrong Way:** Ask AI "Is my system healthy?" (It guesses).
*   **Our Way:**
    1.  Python script fetches real metrics from `Observability API`.
    2.  Python script inserts metrics into the prompt.
    3.  AI analyzes the *provided* metrics.

### 3. The Persona
We configured the System Prompt to enforce professional behavior:
> *"You are a Senior Site Reliability Engineer. Analyze the following telemetry. Cite evidence (error rates) and suggest root causes."*

---

## 🧪 The "Fire Drill" (Verification)

We tested the agent against a simulated outage.

### Step 1: The Setup
We simulated a partial database failure using our Phase 3 Chaos API:
```bash
# Inject 30% failure rate + 2 second latency
curl -X POST http://localhost:8002/chaos -d '{"failure_rate": 0.3, "latency_ms": 2000}'
```

### Step 2: The Inquiry
We asked the Agent: *"Why is service-b so slow?"*

### Step 3: The Result
**Raw Data (Invisible to User):**
```json
{"status": "DEGRADED", "errorRate": 13.24}
```

**AI Analysis (Returned to User):**
> "Based on the telemetry, **Service B is DEGRADED**.
> The primary indicator is a high **error rate of 13.24%**.
> This suggests a persistent software bug or a failing downstream dependency.
> Recommendation: Check application logs for 5xx patterns."

---

## 🧠 Critical Engineering Lessons

### 1. The "Blind Spot" (Latency)
**Observation:** We injected a 2-second latency, but the AI *only* talked about the Error Rate.
**Reason:** Our `Observability API` (Phase 2) only returned `requestRate` and `errorRate`. It did not return `p95_latency`.
**Lesson:** An AI is only as smart as the data interfaces you build for it. **Observability API design determines AI insight quality.**

### 2. Metric Lag
**Observation:** When we stopped the chaos, the AI still said "DEGRADED" for 2 minutes.
**Reason:** Prometheus calculates rates over a sliding window (`[2m]`).
**Lesson:** Operational AI needs to understand time. A system isn't "broken" if the error happened 5 minutes ago.

---

## 📂 Final Project Structure

```text
ai-observability-platform/
├── .env                     # API Keys (Gemini)
├── docker-compose.yml       # Orchestrates 6 containers
├── service_a/               # Traffic Generator
├── service_b/               # Chaos Target
├── observability-api/       # The Tool (GraphQL)
├── ai-agent/                # The Brain (FastAPI + LLM)
│   ├── main.py              # Agent Logic
│   ├── llm_client.py        # Strategy Pattern
│   └── Dockerfile
└── platform/                # Prometheus & Grafana Configs
```

---

## 🚀 How to Run Phase 4

1.  **Configure:** Add `GEMINI_API_KEY` to `.env`.
2.  **Start:** `docker-compose up --build -d`
3.  **Interact:**
    ```bash
    curl -X POST http://localhost:8090/analyze \
      -H "Content-Type: application/json" \
      -d '{"query": "Is the system healthy?"}'
    ```

---

### ✅ Project Completion: Manual Instrumentation Edition
We have successfully built a full loop:
**Code -> Logs/Metrics -> Tracing -> API -> Chaos -> AI Analysis.**

*Next Step: Zero-Code Auto-Instrumentation with OpenTelemetry.*