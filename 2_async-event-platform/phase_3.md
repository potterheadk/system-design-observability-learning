# 📄 Phase 3: The Background Worker (Consumer)

## 1. The Core Concept: The Worker Pattern
In Phase 2, we filled the queue (Redis) with jobs.
In Phase 3, we built the **Consumer**: a dedicated service that does nothing but listen to the queue and crunch numbers.

**Why separate the Worker?**
1.  **Scaling:** If traffic spikes, we can run 1 API container and **50 Worker containers**. The API stays fast, and the work gets distributed.
2.  **Resource Isolation:** The API is "I/O Bound" (lots of network connections). The Worker is "CPU Bound" (heavy calculation). We can give the Worker a huge GPU without wasting it on the API.

## 2. The Architecture (Pipeline)

We added a new container service: `worker`.

```ascii
 [ Redis Stream ] ◀──(1) Pull (XREADGROUP) ── [ Worker Service ]
      │                                             │
      │                                             │ (2) Processing...
      │                                             │     (time.sleep 5)
      │                                             │
      │                                             │ (3) Save Result
      ▼                                             ▼
 [ Job Data ] ◀──────(HSET job:123)─────────── [ Result Hash ]
```

## 3. Tools & Concepts Used

### 👥 Redis Consumer Groups
*   **Concept:** Instead of just "reading" a message, we join a **Group**.
*   **The Command:** `XREADGROUP GROUP ai_processors CONSUMER worker-1`.
*   **Why?**
    *   **Load Balancing:** If we start `worker-2`, Redis automatically distributes the jobs. Worker 1 gets Job A, Worker 2 gets Job B.
    *   **Reliability:** If Worker 1 takes a job but doesn't finish it, Redis remembers "Job A is pending for Worker 1." It doesn't get lost.

### 📝 HSET (Hash Set)
*   **Role:** The "Database" for our results.
*   **Structure:**
    *   Key: `job:8b02...`
    *   Fields: `status="completed"`, `result="Summary..."`.
*   **Why Redis for Storage?** It is fast and simple for this homelab project. In production, we might write the final result to PostgreSQL or S3, but keep the *status* in Redis.

### 🔄 The Event Loop (Worker Logic)
The worker is an infinite loop:
1.  **Poll:** "Hey Redis, any work?" (Blocking wait for 5s to save CPU).
2.  **Work:** Run the heavy function.
3.  **Ack:** Tell Redis "I'm done" (`XACK`).

## 4. The Experiment (The Pipeline Flow)

**Action:**
We submitted a job: `POST /analyze` → `{"status": "queued"}`.

**Observation (Logs):**
1.  **API:** Responded instantly.
2.  **Worker Logs:**
    *   `👷 Waiting for jobs...`
    *   *(Request Submitted)*
    *   `📥 Processing Job...`
    *   *(5 Seconds Later)*
    *   `✅ Job Completed.`

**Conclusion:** The system is now fully functional. The user submits, the API acknowledges, and the Worker processes. But the user still doesn't *know* the result.

---

### ✅ End of Phase 3 Documentation
We have successfully implemented **Asynchronous Processing**.
