Arch Linux with a resource-constrained laptop, we will play this smart.

**The Strategy for Low-End Hardware:**
1.  **Driver:** Use the `docker` driver. It avoids creating a heavy VirtualBox/KVM VM. It runs K8s nodes as Docker containers.
2.  **Resources:** We will set explicit CPU/Memory limits so K8s doesn't eat your browser's RAM.
3.  **Components:** We will deploy **only** the Core App (Redis, API, Worker) first. We will skip the Observability stack (Jaeger/Prometheus) for now to save RAM.

---

# ☸️ Project: Migrating to Kubernetes
**Phase 1: The Basics (Deployments & Services)**

## 1. The Mental Shift (Compose vs K8s)
In Docker Compose, you write one file (`docker-compose.yml`).
In Kubernetes, we break things down:

| Docker Compose | Kubernetes Equivalent | Purpose |
| :--- | :--- | :--- |
| `service: api` | **Deployment** | Manages the Apps (Replica count, Updates) |
| `ports: 8000:8000` | **Service** | Manages Networking (IPs, Load Balancing) |
| `environment:` | **ConfigMap** | Stores variables (REDIS_HOST) |
| `volumes:` | **PersistentVolume** | Stores data (Redis persistence) |

---

## 🛠️ Step 1: Start Minikube (The Right Way)

Since you already have Docker installed, use it as the driver. It's lighter.

```bash
# 1. Start Cluster with limit on RAM/CPU (Adjust to your laptop)
# Example: 2GB RAM, 2 CPUs. (K8s needs at least 1.8GB usually)
minikube start --driver=docker --memory=2200cpus=2

# 2. Check if it's alive
kubectl get nodes
```
*Expectation:* You should see one node named `minikube` with status `Ready`.

---

## 🛠️ Step 2: The "Image" Trick

**The Problem:**
K8s usually tries to pull images from Docker Hub. Your images (`blocking-api and worker`) are local. K8s can't see them.

**The Arch Linux Power Move:**
We will point your terminal's Docker client to talk to **Minikube's Docker Daemon**.
This means when you build an image, it builds **inside** the cluster. No pushing/pulling needed.

Run this command (and memorize it):
```bash
eval $(minikube -p minikube docker-env)
```

**Verify it worked:**
Run `docker ps`. You should see K8s internal containers (etcd, coredns), NOT your usual desktop containers.

**Now, Build Your Images (Inside Minikube):**
Go to your `3_kubernetes-migration` folder:
```bash
# Build API
docker build -t my-api:v1 ./blocking-api

# Build Worker
docker build -t my-worker:v1 ./worker
```
*(We name them `my-api:v1` to keep it simple).*

---

## 🛠️ Step 3: Redis ( The Database)

We need Redis running before anything else.
Create a folder for your K8s manifests:
```bash
mkdir k8s
```

Create `k8s/redis.yaml`.
This file contains TWO things: a **Deployment** (running Redis) and a **Service** (letting API talk to Redis).

```yaml
# 1. The Deployment (Runs the Container)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        resources:
          requests: # Minimal resources for your laptop
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "250m"
        ports:
        - containerPort: 6379

---
# 2. The Service (Internal Networking)
apiVersion: v1
kind: Service
metadata:
  name: redis # This allows other pods to reach it at "redis:6379"
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
```

**Apply it:**
```bash
kubectl apply -f k8s/redis.yaml
```

---

## 🛠️ Step 4: The API (The Producer)

Create `k8s/api.yaml`.
Notice `imagePullPolicy: Never`. This tells K8s "Don't go to the internet, use the image I just built locally."

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 1 # We start with 1, we will scale later
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: my-api:v1      # The image we built
        imagePullPolicy: Never # CRITICAL for local dev
        env:
        - name: REDIS_HOST    # Environment variable
          value: "redis"      # Matches the Service name from step 3
        resources:
          requests:
            memory: "100Mi"
            cpu: "100m"
        ports:
        - containerPort: 8000

---
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  type: NodePort # Expose to outside world (sort of)
  selector:
    app: api
  ports:
    - port: 8000      # Internal Port
      targetPort: 8000 # Container Port
      nodePort: 30001  # External Access Port
```

**Apply it:**
```bash
kubectl apply -f k8s/api.yaml
```

---

## 🛠️ Step 5: The Worker (The Consumer)

Workers don't need a `Service` because nobody talks TO them. They talk TO Redis.

Create `k8s/worker.yaml`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: my-worker:v1
        imagePullPolicy: Never
        env:
        - name: REDIS_HOST
          value: "redis"
        resources:
          requests:
            memory: "100Mi"
            cpu: "100m"
```

**Apply it:**
```bash
kubectl apply -f k8s/worker.yaml
```

---

## 🚀 Step 6: Verify and Access

**1. Check status:**
```bash
kubectl get pods
```
*Expectation:* You should see 3 pods (api, redis, worker) with status `Running`.
*If you see `ImagePullBackOff`, it means Step 2 failed (you didn't build the image inside minikube).*

**2. Access the API:**
Since we are using Minikube `docker` driver, `NodePort` isn't reachable via `localhost` directly. We need to tunnel.

Run this in a separate terminal:
```bash
minikube service api-service
```
This will open a browser window OR give you a URL like `http://127.0.0.1:12345`.

**3. Test the Async Flow:**
Use the URL minikube gave you (replace `MINIKUBE_URL`):

```bash
curl -X POST MINIKUBE_URL/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello Kubernetes"}'
```

**4. Check Worker Logs:**
Find the worker pod name:
```bash
kubectl get pods
```
View logs:
```bash
kubectl logs worker-xxxxxxxxx-xxxxx -f
```

**Task:**
Get all 3 pods running green. Submit a job via the Minikube URL. Verify the worker pod processes it.

Once this works, you have officially migrated to **Kubernetes**. Then we will do the fun part: **Scaling**.
