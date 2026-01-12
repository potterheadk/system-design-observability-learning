Here is the comprehensive engineering documentation for **Phase 2 (The Brain)** and **Phase 3 (The Chaos)**.

Save this file as `phases_2_and_3.md` in your repository. It explains the jump from "Passive Monitoring" to "Active Platform Engineering."

---

# 🧠 Phase 2 & 3: The Brain and The Chaos

**Status:** Completed  
**Focus:** Platform APIs & Controlled Failure Injection

## 📖 The Story So Far
In **Phase 1**, we built a system that generates logs and metrics. But we had two problems:
1.  **Data Overload:** To check system health, we had to write complex PromQL queries manually.
2.  **Unpredictability:** Failures were random (hardcoded 10%). We couldn't reliably test alerts because we couldn't force a crash when we wanted one.

In **Phase 2 & 3**, we fixed this by building a **Translator (API)** and a **Remote Control (Chaos)**.

---

## 🔌 Phase 2: The Observability API (The Translator)

### The Problem: "PromQL is Hard"
Prometheus is a great database, but a terrible user interface.
*   **Raw Data:** `http_requests_total{status="500"}` = `2351`
*   **Human Question:** "Is the system healthy?"

We needed a layer to translate raw math into business status (`HEALTHY`, `DEGRADED`, `DOWN`).

### The Architecture
We built a **GraphQL API** (`observability-api`) that acts as the "Brain".

```ascii
      User / Future AI
             │
      (GraphQL Query)
             ▼
┌──────────────────────────┐
│    Observability API     │ ◀── The "Translator"
└────────────┬─────────────┘
             │ Runs PromQL (sum(rate(...)))
             ▼
┌──────────────────────────┐
│       Prometheus         │
└──────────────────────────┘
```

### Key Engineering Decision: The Sliding Window
We learned that "Health" is relative to time.
*   We chose a **2-minute window** (`[2m]`).
*   **Why?** If the system crashes for 1 second, it shouldn't scream "DOWN" immediately. It needs to see a trend.
*   **The Trade-off:** **Metric Lag**. When we fix the system, it takes 2 minutes for the "Average Error Rate" to drop back to zero. We saw this in testing (Status remained `DEGRADED` for a while after fixing chaos).

---

## 🌪️ Phase 3: Chaos Engineering (The Remote Control)

### The Problem: "It works on my machine"
We don't want a system that fails randomly. We want a system that fails **on command** so we can test if our monitoring works.

### The Solution: Chaos-as-Code
We modified **Service B** to include a "Chaos State" in memory.

```python
# Default State (Peace)
chaos_config = {"failure_rate": 0.0, "latency_ms": 0}

# The Injection Point (Middleware)
if random.random() < chaos_config["failure_rate"]:
    raise HTTP_500()
```

We exposed a POST endpoint (`/chaos`) to update this state globally.

### The Experiment Loop
This enabled us to run **Hypothesis-Driven Experiments**:

1.  **Hypothesis:** "If Service B has a 50% failure rate, the Platform API should report status DOWN."
2.  **Action:**
    ```bash
    curl -X POST http://localhost:8002/chaos -d '{"failure_rate": 0.5}'
    ```
3.  **Observation:** API reported `errorRate: 48.5%` and `status: DOWN`.
4.  **Recovery:**
    ```bash
    curl -X POST http://localhost:8002/chaos -d '{"failure_rate": 0.0}'
    ```
5.  **Result:** System returned to `HEALTHY` (after the sliding window cleared).

---

## 🛠️ Technical Implementation Details

### Directory Structure Evolution
We moved from a simple service setup to a modular platform structure:

```text
observability-platform/
├── service_a/           # API Gateway (The Victim)
├── service_b/           # Worker (The Villain - Chaos Enabled)
├── observability-api/   # GraphQL Service (The Brain)
├── platform/            # Prometheus & Grafana configs
└── docker-compose.yml   # The Orchestrator
```

### The GraphQL Schema
We designed a strongly typed schema so our future AI knows exactly what to ask for:

```graphql
type ServiceHealth {
  serviceName: String!
  requestRate: Float!
  errorRate: Float!
  status: String!  # Enum: HEALTHY | DEGRADED | DOWN
}
```

---

## 🚀 How to Demo This Phase

**1. Check Health (Peace Time)**
Go to `http://localhost:8080/graphql`:
```graphql
query {
  getServiceHealth(serviceName: "service-b") {
    status
    errorRate
  }
}
```
*Result:* `HEALTHY`

**2. Inject Chaos (War Time)**
Run in terminal:
```bash
curl -X POST http://localhost:8002/chaos \
  -H "Content-Type: application/json" \
  -d '{"failure_rate": 0.5, "latency_ms": 500}'
```

**3. Verify Impact**
Run the GraphQL query again.
*Result:* `DOWN` (Error Rate > 20%).

---

## 🔮 Next Steps: Phase 4 (The AI Analyst)

Now we have:
1.  **Traces** (Evidence of *what* happened).
2.  **API** (Ability to ask *how* the system is doing).
3.  **Chaos** (Ability to *break* the system).

**The Missing Link:**
When the system is `DOWN`, we still have to manually grep logs to find the JSON trace and understand *why*.

**Phase 4 Goal:**
We will connect an LLM (using OpenAI or Ollama) to our Observability API.
We will ask the AI: *"Why is Service B down?"*
The AI will:
1.  Call `getServiceHealth`.
2.  See the error.
3.  (Future) Query logs.
4.  Explain: *"Service B is failing due to a 50% injected failure rate."*

