This phase focuses on the **Infrastructure** layer: Networking and Storage. Before we run our code, we must ensure the "plumbing" is correct.

---

# 📄 Phase 2: Infrastructure (Networking & Storage)

## 1. The Core Concept: Service Discovery
In Docker Compose, we simply said `depends_on: - redis` and the magic DNS worked.
In Kubernetes, Pods are volatile. They die and respawn with new IP addresses every time.

**The Problem:**
If the API connects to Redis at IP `10.1.1.5`, and the Redis Pod dies and respawns at `10.1.1.6`, the API breaks.

**The Solution: The Service Object**
A **Service** is a stable "Receptionist" that sits in front of the Pods.
1.  We give the Service a name: `redis`.
2.  It gets a stable Virtual IP.
3.  The API connects to `redis:6379`.
4.  The Service forwards the packet to whatever Redis Pod happens to be alive.

```ascii
[ API Pod ] ──(Connects to "redis")──▶ [ Service: Redis ] ──(Forwards)──▶ [ Pod: Redis-5498 ]
                                       (Static IP)                        (Dynamic IP)
```

## 2. The Core Concept: Persistence (PVC)
In our early experiments, we found a critical flaw: **Data Amnesia.**
When we deleted the Redis Pod, all jobs and statuses vanished. This is because, by default, Pod file systems are **Ephemeral** (temporary).

**The Solution: Persistent Volume Claims (PVC)**
We need to treat storage like an external Hard Drive, not like RAM.

1.  **PVC (The Request):** "I need 1GB of storage."
2.  **PV (The Disk):** K8s finds a physical disk (or creates a file in Minikube).
3.  **Mounting:** K8s plugs this disk into the Pod at `/data`.

```ascii
[ Pod: Redis (Old) ] ──plugged into──▶ [ Disk: PVC-1 ] 📦 (Data: Job 123)
       │
    (🔥 Pod Dies)
       │
[ Pod: Redis (New) ] ──plugged into──▶ [ Disk: PVC-1 ] 📦 (Data: Job 123)
                                       (Data Survives!)
```

## 3. Implementation Details

### The Redis YAML (`k8s/redis.yaml`)
We defined the Deployment and Service in one file.

**Key Configurations:**
*   **Selector:** `app: redis`. This tells the Service "Look for any pod labeled `redis`."
*   **AppendOnly:** `command: ["redis-server", "--appendonly", "yes"]`. This forces Redis to write every change to disk immediately.

### The Storage YAML (`k8s/redis-pvc.yaml`)
We created a separate claim.

**Key Configurations:**
*   **AccessMode:** `ReadWriteOnce`. This means "Only one pod can mount this at a time." (Standard for databases to prevent corruption).
*   **Capacity:** `1Gi`. Enough for thousands of job IDs.

## 4. The "Survival Test" (Verification)
We proved the architecture worked with a destructive test.

1.  **Action:** We submitted a "Golden Job" (`ID: 1577...`).
2.  **Verification:** API returned `{"status": "queued"}`.
3.  **Destruction:** We ran `kubectl delete pod -l app=redis`.
4.  **Observation:**
    *   The Old Pod terminated.
    *   The New Pod started.
    *   K8s detached the "Disk" from the old one and reattached it to the new one.
5.  **Result:** We queried the API again. It returned the job status successfully. **Data persisted.**

---

### ✅ End of Phase 2
We now have a stable, persistent database layer.

