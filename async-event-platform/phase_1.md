This is the **Master Documentation Series** for the **Distributed Async Task Queue** project.

# 📘 Project: Async Task Queue & Event Pipeline
# 📄 Phase 1: The Blocking Baseline (Synchronous)

## 1. The Core Concept: Synchronous vs. Asynchronous
Before building complex queues, we established a **Baseline**. We built a standard REST API where the client waits for the server to finish the job.

**Analogy:**
*   **Synchronous (Phase 1):** You call a restaurant to order pizza. You stay on the phone line for 20 minutes until the pizza is baked. You cannot do anything else (Block).
*   **Asynchronous (Later Phases):** You call, they say "Order #123 is placed", and hang up. You call back later to check status (Polling), or they SMS you when done (Callback).

## 2. The Architecture (Blocking)

In this phase, we simulated a "Heavy AI Task" using `time.sleep(5)`.

```ascii
      User A                      Server (Single Worker)
        │                                  │
        │ (1) POST /analyze                │
        │─────────────────────────────────▶│
        │                                  │ 🛑 PROCESSING (5s)
        │       (User Waits...)            │ 🛑 Thread Blocked
        │                                  │
        │                                  │
      User B                               │
        │ (2) GET /health                  │
        │─────────────────────────────────▶│ ❌ REJECTED / DELAYED
        │       (User B Waits...)          │ (Server is busy with User A)
        │                                  │
        │ (3) User A Response (200 OK)     │
        │◀─────────────────────────────────│ ✅ User A Done
        │                                  │
        │ (4) User B Response (200 OK)     │
        │◀─────────────────────────────────│ ✅ User B Finally Done
```

## 3. The "Cardinal Sin" of Python APIs
We discovered a critical behavior in Python's `asyncio` Event Loop.

### The Code
```python
@app.post("/analyze")
async def analyze(request):
    time.sleep(5)  # <--- THE KILLER
    return {"status": "done"}
```

### Why this is dangerous
Python uses a **Global Interpreter Lock (GIL)** and a single **Main Event Loop** for async code.
1.  **`async def`**: Tells FastAPI "Run this on the main highway."
2.  **`time.sleep(5)`**: A command that stops all traffic on the highway.
3.  **Result:** The entire server freezes. No other request (even a tiny health check) can enter until the sleep finishes.

**Production Impact:** One malicious user sending heavy requests can DoS (Denial of Service) your entire platform without checking bandwidth.

## 4. The Experiment (Proof of Failure)
We ran two requests simultaneously using a shell script:

```bash
# Request A (Heavy) starts at 00:00:01
# Request B (Light) starts at 00:00:02
```

**Observation:**
*   Request A finished at `00:00:06` (5s duration).
*   Request B finished at `00:00:06` (4s duration, waiting for A).
*   **Conclusion:** The system is **Coupled** and **Blocking**.

## 5. Tools & Concepts Used

### ⚡ FastAPI (Synchronous Mode)
*   **What is it?** A modern Python web framework.
*   **Phase 1 Role:** Serving the HTTP endpoint.
*   **Lesson:** Using `def` vs `async def` matters. Regular `def` runs in a thread pool (safer for blocking code), while `async def` runs on the main loop (dangerous for blocking code).

### 🦄 Uvicorn (The Worker)
*   **What is it?** The ASGI Web Server. It listens to the network port and passes requests to FastAPI.
*   **Configuration:** We used `--workers 1`.
*   **Why?** To simulate a resource-constrained container. In Kubernetes, pods often have limited CPU, mimicking this single-worker constraint.

