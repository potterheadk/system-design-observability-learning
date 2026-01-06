
# 🔭 AI-Assisted Observability & Chaos Platform

**Status:** Phase 1 Complete (Baseline + Tracing)  
**Goal:** Build a platform to understand distributed failures using Observability, Chaos Engineering, and (eventually) AI.

## 🏗️ System Architecture (Current State)

We have built a "Call Chain" to simulate a microservices environment.

```ascii
User Request (curl)
     │
     ▼
┌──────────────┐   HTTP (Headers: x-request-id)    ┌──────────────┐
│  Service A   │ ────────────────────────────────▶ │  Service B   │
│ (API Gateway)│           (Propagates ID)         │   (Worker)   │
└──────┬───────┘                                   └──────┬───────┘
       │                                                  │
       │ JSON Logs (stdout)                               │ JSON Logs (stdout)
       │ Metrics (/metrics)                               │ Metrics (/metrics)
       ▼                                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                           Prometheus                             │
│                    (Scrapes every 5 seconds)                     │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
                             Grafana
                        (Visual Dashboard)
```

## 🧠 Engineering Concepts Learned

### 1. The "RED" Method (Metrics)
We instrumented services to expose the three golden signals of microservices:
*   **Rate:** How many requests per second? (via `http_requests_total`)
*   **Errors:** How many 500s? (Service B fails 10% of the time by design).
*   **Duration:** How long did it take? (Latencies simulated 0.1s - 0.3s).

### 2. Structured Logging vs. Text
*   **Old Way:** `INFO: User login failed` (Hard to grep, hard to automate).
*   **New Way (Structlog):** `{"event": "login_failed", "user_id": 123}`.
*   **Why:** Machines can parse JSON. This prepares us for AI analysis later.

### 3. Distributed Tracing (Context Propagation)
The hardest part of distributed systems is answering: *"Service A failed, but did Service B cause it?"*
*   **Solution:** We generate a `UUID` in Service A.
*   **Propagation:** We pass this UUID in the `x-request-id` HTTP header to Service B.
*   **Result:** We can grep the logs of *both* services using the same ID to see the full story.

### 4. Docker Engineering
*   **The Build Trap:** Learned that changing Python code requires `docker-compose up --build`.
*   **Ghost Containers:** Learned that `force-recreate` is sometimes needed to flush old layers.
*   **Networking:** Service A talks to Service B via Docker DNS (`http://service-b:8000`).

---

## 🛠️ How to Run

1.  **Start the Stack:**
    ```bash
    docker-compose up --build -d
    ```

2.  **Generate Traffic (The "Noise" Maker):**
    Run this in a separate terminal to simulate users:
    ```bash
    while true; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8001/chain; sleep 0.5; done
    ```

3.  **Access Dashboards:**
    *   **Prometheus:** [http://localhost:9090](http://localhost:9090)
    *   **Grafana:** [http://localhost:3000](http://localhost:3000) (admin/admin)

---

## 🕵️ Verification Manual (The "Sherlock Test")

### 1. Check Metrics
Query Prometheus: `rate(http_requests_total{status="500"}[1m])`
*   **Success:** Should show a non-zero number for `service-b`.

### 2. Trace a Request
Find an error in Service A and trace it to Service B.

**Step A: Get ID from Service A**
```bash
docker logs observability-platform-service-a-1 | grep "upstream_failed" | tail -n 1
```
*(Copy the `request_id`)*

**Step B: Find it in Service B**
```bash
docker logs observability-platform-service-b-1 | grep "PASTE_ID_HERE"
```
*   **Success:** You see a JSON log from Service B with the matching ID.

---

## 🗺️ Roadmap

- [x] **Phase 0: Baseline:** Two services talking to each other.
- [x] **Phase 1: Better Signals:** Structured Logs (JSON) & Distributed Tracing.
- [ ] **Phase 2: Platform API:** GraphQL API to query system health programmatically.
- [ ] **Phase 3: Chaos:** Injecting latency and crashes on purpose.
- [ ] **Phase 4: AI Analysis:** Using LLMs to explain *why* the chaos caused the failure.

---

### 🛑 Checkpoint
