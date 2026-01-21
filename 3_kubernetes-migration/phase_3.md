This phase covers the actual **Business Logic**: The API (Producer) and the Worker (Consumer). This is where the code meets the cluster.

---

# 📄 Phase 3: The Application Layer (Deployments & Scaling)

## 1. The Core Concept: Stateless Deployments
In Phase 2, we treated Redis delicately because it held **State** (Data).
In Phase 3, we treat the API and Workers as **Stateless**.
*   **API:** Just takes HTTP requests and pushes to Redis. Doesn't save anything to disk.
*   **Worker:** Just pulls from Redis and computes. Doesn't save anything to disk.

**Why this matters:**
Because they are stateless, we can:
1.  **Kill them** at random without losing data.
2.  **Scale them** to 100 replicas instantly.
3.  **Upgrade them** without downtime.

## 2. The Producer (API Gateway)

### The Deployment (`k8s/api.yaml`)
We defined the API with a specific constraint: **Accessibility**.

*   **Service Type: NodePort:**
    *   In Docker Compose, we mapped `8001:8000`.
    *   In K8s, `NodePort` opens a specific port (e.g., `30001`) on the Virtual Machine so we can reach it from our laptop.
    *   *Note:* In real clouds (AWS/GCP), this would be a `LoadBalancer` type.

### The Connection (`env` vars)
How does the API find Redis?
In Docker Compose, it was magic (`REDIS_HOST=redis`).
In Kubernetes, it is explicit.

```yaml
env:
  - name: REDIS_HOST
    value: "redis" # Matches the metadata.name of the Redis Service
```
The K8s internal DNS resolves string `"redis"` to the Cluster IP of the Redis Service.

## 3. The Consumer (Worker Fleet)

### The Deployment (`k8s/worker.yaml`)
This is a pure "Background Process."
*   **No Service:** Notice there is **no** `Service` YAML for the worker.
    *   *Why?* Nobody sends HTTP requests *to* the worker. The worker initiates the connection *out* to Redis. It is invisible to the outside world.

### The Scaling Magic
This was the highlight of the migration.
*   **Docker Compose:** Scaling is a configuration change + restart.
*   **Kubernetes:** Scaling is an API call.

```bash
kubectl scale deployment worker --replicas=3
```

**What happened under the hood:**
1.  K8s Scheduler saw the request: "Desired: 3, Current: 1".
2.  It found free CPU/RAM on the Node.
3.  It booted 2 new Pods.
4.  Redis (Consumer Groups) automatically detected the new clients and started sharing the load (Round-Robin distribution).

## 4. The Self-Healing Code (Robustness)

We encountered a critical race condition during migration:
*   **The Crash:** The Worker started *before* Redis was ready.
*   **The Error:** `NOGROUP` (Consumer Group didn't exist).
*   **The Fix:** We rewrote `worker/main.py` to be **Self-Healing**.
    *   Instead of crashing, it catches the `NOGROUP` error.
    *   It runs a repair function (`ensure_consumer_group`).
    *   It retries.

This transformed our worker from a "Fragile Script" to a "Resilient Daemon" capable of surviving total infrastructure failure.

## 5. Zero-Downtime Rollouts

We demonstrated the power of **Rolling Updates**.
1.  We changed the code (v2, v3).
2.  We commanded K8s: `kubectl set image ... worker=my-worker:v3`.
3.  **The Choreography:**
    *   K8s started a v3 pod.
    *   Waited for it to be healthy.
    *   Terminated a v2 pod.
    *   Repeated until all were v3.

**Result:** The queue continued processing jobs seamlessly while the software was upgraded.

---

### ✅ End of Phase 3
We have a fully functional, auto-healing, persistent, scalable distributed system running on Kubernetes.

