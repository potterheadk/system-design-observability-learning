# 🛠️ Tools & Techniques Explained

This document serves as a technical reference for the concepts used in the **AI-Assisted Observability Platform**.

---

## 1. The Core Infrastructure

### 🐳 Docker & Docker Compose
**What is it?**
A containerization platform. Think of it as a "shipping container" for code. It packages the code, python version, and libraries into a single block.

**Why we used it:**
*   **Isolation:** `Service A` and `Service B` have their own file systems and don't fight over dependencies.
*   **Networking:** Docker Compose creates a private network where services can talk by name (`http://service-b`) instead of IP addresses.

---

## 2. The Application Layer

### ⚡ FastAPI (Python)
**What is it?**
A modern, high-performance web framework for building APIs with Python.

**Why we used it:**
*   It supports **Async/Await** natively (critical for high throughput).
*   It automatically generates documentation (Swagger UI).
*   It is the standard for Python-based Microservices and AI wrappers.

---

## 3. Observability: Metrics (The "Health Check")

### 🔥 Prometheus
**What is it?**
A Time-Series Database (TSDB). It is designed to store **Numbers** over **Time**.
*   *Example:* "At 12:00, CPU was 50%. At 12:01, CPU was 60%."

**How it works (The Pull Model):**
Prometheus is active. It wakes up every 5 seconds (scraping interval) and visits `http://service-a:8000/metrics`. It "pulls" the data.

**Visual Concept:**
```ascii
[ Service A ] ◀──(Scrape)── [ Prometheus ]
{ 404_errors: 5 }               | Stores: 12:00 -> 5
```

### 📊 Grafana
**What is it?**
The Dashboard tool. Prometheus stores the data; Grafana makes it look pretty.

**Why we used it:**
Raw Prometheus data looks like text. Grafana turns it into Line Graphs, Heatmaps, and Gauges that humans can read instantly.

---

## 4. Observability: Tracing (The "Investigation")

### 🕵️ OpenTelemetry (OTel)
**What is it?**
An open standard for generating signals (Metrics, Logs, and Traces). It is **vendor-neutral** (it doesn't care if you use Jaeger, Datadog, or Google Cloud).

**The Auto-Instrumentation Agent:**
We used the OTel Python Agent. It "wraps" our code at startup. It listens for library calls (like `requests.get`) and measures how long they take.

### 🐇 Jaeger
**What is it?**
A Distributed Tracing System. It connects the dots between microservices.

**The Concept: The Waterfall**
Prometheus tells you *that* an error happened. Jaeger tells you *where* and *why*.

```ascii
[ Service A (Total: 500ms) ]
      ⬇
      [ Service B (Total: 480ms) ] ───▶ [ ❌ Error: 500 ]
```
**Why we used it:**
To visualize the "Chain" of requests. Without Jaeger, we wouldn't know if Service A was slow because of its own code or because it was waiting for Service B.

---

## 5. Reliability Engineering

### 🌪️ Chaos Engineering
**What is it?**
The discipline of experimenting on a system to build confidence in its capability to withstand turbulent conditions.

**How we implemented it:**
We built a **Remote Control** (`POST /chaos`).
*   **Hypothesis:** "If Service B slows down by 2 seconds, Service A should report an error."
*   **Experiment:** Inject 2000ms latency.
*   **Observation:** Check Prometheus/Jaeger.

**Why:**
"Hope is not a strategy." We don't hope our alerts work; we break the system to *prove* they work.

---

## 6. The Intelligence Layer

### 🤖 LLM Agents (Large Language Models)
**What is it?**
An AI (Gemini/Ollama) configured to act as a Site Reliability Engineer (SRE).

**Technique: Tool Use (Grounding)**
We didn't just ask the AI "Is the system healthy?". The AI has no eyes.
1.  **Code Fetch:** Python script calls our internal Observability API.
2.  **Context Injection:** We paste that data into the prompt: *"The error rate is 13%."*
3.  **Reasoning:** The AI reads the data and generates an explanation.

**Visual Flow:**
```ascii
User ──▶ [ Agent ] ──▶ [ Get Data ] ──▶ [ Prometheus ]
            │              │
            ◀──────────────┘
       (Analyzes Data)
            │
            ▼
       "The system is DEGRADED due to..."
```

---

## 7. The Golden Signals (The RED Method)
Throughout the project, we focused on the **RED** method for microservices:

1.  **R - Rate:** How many requests per second?
2.  **E - Errors:** How many requests failed?
3.  **D - Duration:** How long did they take?

These are the three numbers that matter most when keeping a system alive.
```