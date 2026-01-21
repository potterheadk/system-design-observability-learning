# ☸️ Project 3: Kubernetes Migration & Orchestration

**Goal:** Take a distributed async application and deploy it to a self-healing, scalable Kubernetes cluster.
**Prerequisites:** Mastery of Docker Compose (Project 2).

---

# 📘 Phase 1: The Architecture Shift

## 1. Docker Compose vs. Kubernetes
In Project 2, we used **Docker Compose**.
*   **Concept:** "Run these containers on my laptop."
*   **Limitation:** If a container died, it stayed dead (unless we manually restarted). If we wanted 5 workers, we had to manually scale them. It is **Imperative** (Do this now).

In Project 3, we move to **Kubernetes (K8s)**.
*   **Concept:** "Here is my desired state. Make it happen."
*   **Benefit:** It is **Declarative**. We say "I want 3 workers." K8s ensures there are always 3. If one crashes, K8s acts as a robot manager and replaces it immediately.

## 2. Visual Architecture

### Docker Compose Architecture (The "Pet" Model)
We treat containers like pets. We name them (`worker-1`), we watch them, and we fix them when they get sick.

```ascii
[ Laptop / Host OS ]
      │
      ├── [ API Container (Port 8000) ]
      ├── [ Redis Container (Port 6379) ]
      └── [ Worker Container ]
```

### Kubernetes Architecture (The "Cattle" Model)
We treat pods like cattle. We don't care about their names (`worker-xv9z`). If one gets sick, we replace it.

```ascii
[ Kubernetes Cluster (Minikube) ]
      │
      ├── [ Node (The Virtual Machine) ]
      │     │
      │     ├── [ Service: API-Gateway (Load Balancer) ]
      │     │      │
      │     │      ├── [ Pod: API (Replica 1) ]
      │     │      └── [ Pod: API (Replica 2) ]
      │     │
      │     ├── [ Service: Redis-Internal ]
      │     │      │
      │     │      └── [ Pod: Redis (Stateful) ] ── [ PVC Disk ]
      │     │
      │     └── [ Deployment: Workers ]
      │            ├── [ Pod: Worker-1 ]
      │            ├── [ Pod: Worker-2 ]
      │            └── [ Pod: Worker-3 ]
```

## 3. Core Kubernetes Concepts

### 📦 Pods (The Atoms)
*   **What is it?** The smallest unit in K8s. It wraps your container.
*   **Analogy:** If Docker is the "Engine", a Pod is the "Car" that wraps the engine, tires, and seats.
*   **Life Cycle:** Ephemeral. They are born, they live, they die. We never restart a pod; we replace it.

### 🏭 Deployments (The Factory)
*   **What is it?** It manages Pods. You tell the Deployment: "I want 3 copies of the Worker image."
*   **Superpower:** **Self-Healing.** The Deployment constantly watches the cluster. If you delete a Worker pod manually, the Deployment notices the count dropped to 2, and instantly creates a new one to get back to 3.

### 📞 Services (The Receptionist)
*   **What is it?** A stable network address.
*   **The Problem:** Since Pods die and respawn, their IP addresses change constantly. The API cannot trust the IP of Redis.
*   **The Solution:** The **Service** gets a static IP (`redis:6379`). It forwards traffic to whatever Redis pod happens to be alive at that moment.

---

## 4. Docker Internal Architecture (The Minikube Trick)

One of the biggest hurdles in this project was **Image Management**.

### The "Registry" Problem
1.  Normally, K8s pulls images from the internet (Docker Hub).
2.  Our images (`my-api`, `my-worker`) are custom and live on our laptop.
3.  K8s cannot see our laptop's Docker storage.

### The Solution: `eval $(minikube docker-env)`
We used a powerful Linux trick to rewire our terminal.

```ascii
Before Command:
[ Terminal ] ── build ──▶ [ Laptop Docker Daemon ] ◀──X── [ Minikube Cluster ]
                               (Images live here)            (Cannot see them)

After Command:
[ Terminal ] ── build ──▶ [ Minikube Docker Daemon ] ◀──OK── [ Minikube Cluster ]
                               (Images live INSIDE)            (Can pull 'Never')
```

*   **Command:** `eval $(minikube -p minikube docker-env)`
*   **Effect:** It tells your local `docker` CLI to talk to Minikube's Docker Engine instead of your laptop's engine.
*   **Result:** When we ran `docker build`, the image was created directly inside the cluster's brain. We could then set `imagePullPolicy: Never` in our YAMLs.

---

### ✅ End of Phase 1
We have established the mental model. We are moving from **Running Containers** to **Managing State**.
