Here is the documentation for **Phase 4**.

---

# 📄 Phase 4: Closing the Loop (State & Polling)

## 1. The Core Concept: Visibility
In Phase 3, the work was getting done, but the User was blind. They had a ticket number (`job_id`) but no way to know if the kitchen was still cooking or if the food was ready.

**The Solution: The Polling Pattern**
We implemented an endpoint that answers the question: *"Is it done yet?"*
This transforms the system from a "Black Box" into a "Transparent Process."

## 2. The Architecture (State Machine)

We introduced a shared **State Store** (Redis Hash) that both the API and Worker can access.

```ascii
      User                        API Gateway                     Redis (Hash)
        │                              │                               │
(1) POST /analyze                      │                               │
        │─────────────────────────────▶│ (2) HSET status="queued"      │
        │                              │──────────────────────────────▶│
        │◀─────────────────────────────│                               │
(3) Return job_id                      │                               │
        │                              │                               │
        │                              │                               │
(4) GET /status/123                    │                               │
   (Polling)  ────────────────────────▶│ (5) HGET job:123              │
                                       │──────────────────────────────▶│
                                       │                               │
                                       │◀──────────────────────────────│
        │◀─────────────────────────────│ (6) Return {"status": ...}    │
   (Result)                            │                               │
```

## 3. The State Lifecycle

We defined a strict lifecycle for every job to ensure data consistency.

1.  **Initialization (API Side):**
    *   Before pushing to the queue, the API creates the entry in Redis: `status="queued"`.
    *   *Why?* Race condition prevention. If the Worker is super fast, it might try to update the job before the API creates it. Or if the User polls immediately (0ms), they shouldn't get a "404 Not Found".

2.  **Transition (Worker Side - Phase 5 Preview):**
    *   Worker picks up job → Updates to `status="processing"`.
    *   Worker finishes job → Updates to `status="completed"`.

## 4. Tools & Concepts Used

### 🔄 Short Polling
*   **What is it?** The client repeatedly calls the API at intervals (e.g., every 2 seconds) to check status.
*   **Pros:** Easiest to implement. Works over standard HTTP.
*   **Cons:** Wastes bandwidth (many requests return "Not Done").
*   **Alternative (Future):** WebSockets or Long Polling (Server pushes updates). For this phase, Polling is the standard engineering baseline.

### 🗄️ Redis Hashes (`HSET`/`HGETALL`)
*   **Structure:** We used a HashMap for each job.
    ```json
    "job:123": {
        "status": "completed",
        "submitted_at": "12:00:00",
        "result": "AI Summary..."
    }
    ```
*   **Benefit:** We can update individual fields (like just the status) without rewriting the whole object.

## 5. The Experiment (The User Experience)

**Action:**
1.  User submits job → Gets `job_id`.
2.  User Polls immediately → API returns `{"status": "queued"}`.
3.  User waits 5 seconds.
4.  User Polls again → API returns `{"status": "completed", "result": "..."}`.

**Conclusion:**
We have successfully closed the feedback loop. The user can now asynchronously submit work and reliably retrieve the result.

---

### ✅ End of Phase 4 Documentation
We have a working, user-friendly async system.
