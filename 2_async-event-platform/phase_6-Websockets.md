**Real-Time Event-Driven Architecture**.
*   **No Refreshing.**
*   **No Polling.**
*   **Just Magic.**

This is exactly how **Uber** updates the car location on your map, or how **Slack** shows a new message.

# 📡 Phase 6: Real-Time Updates (WebSockets & Pub/Sub)

**Status:** Completed
**Technology:** FastAPI WebSockets, Redis Pub/Sub, AsyncIO
**Goal:** Eliminate "Polling" and push updates to the user the instant a job is done.

## 1. The Core Concept: Push vs. Pull
*   **Pull (Phase 4):** The user asks "Are you done?" every 2 seconds. This wastes bandwidth and API resources.
*   **Push (Phase 6):** The user opens a permanent line (WebSocket). The server speaks only when there is news.

## 2. The Architecture (The Bridge)
This phase required bridging two different worlds:
1.  **The Worker:** A background process that doesn't know about HTTP or WebSockets.
2.  **The User:** A browser waiting on a WebSocket.

**The Solution: Redis Pub/Sub**
Redis acts as the common language.

```ascii
[ Worker ] ──(Publish)──▶ [ Redis Channel ] ◀──(Subscribe)── [ API Gateway ]
   │                           "job:123"                          │
   │                                                              │
(Job Done)                                                 (Forward Msg)
   │                                                              │
   ▼                                                              ▼
[ DB Update ]                                               [ User Browser ]
```

## 3. Implementation Details

### The Worker (The Broadcaster)
We modified the worker to **Publish** an event immediately after saving the result.
```python
# Worker Logic
r.hset(job_id, ...) # Save to DB
r.publish(f"job_updates:{job_id}", json_result) # Broadcast
```

### The API (The Listener)
We implemented an **Async WebSocket Endpoint**.
*   **Challenge:** Redis-py is synchronous (blocking). We cannot block a WebSocket.
*   **Solution:** We used `redis.asyncio` (aioredis).
*   **Logic:**
    1.  User connects to `ws://api/ws/job/{id}`.
    2.  API subscribes to Redis channel `job_updates:{id}`.
    3.  API enters an infinite loop: `async for message in pubsub.listen()`.
    4.  When Redis gets a message, API forwards it to `websocket.send_text()`.

### The CORS Issue
We learned that browsers enforce security boundaries. We had to add `CORSMiddleware` to FastAPI to allow our local HTML file to connect to the API container.

## 4. The User Experience
*   **Before:** User clicked "Start", then sat looking at "QUEUED" until they manually refreshed or the polling script checked.
*   **After:** User clicks "Start", waits 5 seconds, and the status flips to "COMPLETED" **instantly** (sub-millisecond latency from worker finish).

## 5. Summary of the Async Platform
We have built a complete, production-grade asynchronous platform.
1.  **Ingestion:** Fast API with Redis Streams.
2.  **Processing:** Scalable Workers (Consumer Groups).
3.  **Reliability:** Try/Catch, Dead Letter Logic, and State Machines.
4.  **Observability:** Auto-Instrumentation with Jaeger.
5.  **Notification:** Real-Time WebSockets.


# 🚢 Next Destination: Kubernetes (K8s)

You have mastered **Docker Compose**.
*   Docker Compose is great for **Development** (1 machine).
*   Kubernetes is for **Production** (100 machines).

**The Challenge:**
In Docker Compose, if the `worker` crashes, it restarts (if we tell it to).
In Kubernetes, if a *Server* crashes, K8s moves the `worker` to a different server automatically. It handles "Scaling", "Self-Healing", and "Rolling Updates" (updating code without stopping the app).

**Our Mission:**
Take this exact **Async Platform** (API, Worker, Redis) and deploy it to a **Local Kubernetes Cluster**.

**Prerequisites:**
You need a local K8s cluster. Since we are on Linux the great Arch BTW, I recommend **Kind** (Kubernetes in Docker) or **Minikube**.
