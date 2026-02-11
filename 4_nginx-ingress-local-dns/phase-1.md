# 🌐 Phase 1: Advanced Networking (Ingress & Reverse Proxies)

**Status:** Completed  
**Technology:** Nginx Ingress Controller, Kubernetes Ingress Resources, DNS Spoofing  
**Goal:** Replace ephemeral IP/Ports (`192.168.49.2:30001`) with production-grade Domain Routing (`http://async.local`).

## 1. The Core Concept: The "Front Door" Problem

### The Old Way: NodePort
In previous projects, we used `NodePort`. This opens a specific port (e.g., `30001`) on every server in the cluster.
*   **The Flaw:** If you have 50 microservices, you need to manage 50 port numbers. Users hate typing `google.com:30001`. It also exposes your internal nodes directly to the internet (security risk).

### The New Way: Ingress
**Ingress** is not a Service; it is a **Smart Router** (Layer 7 Load Balancer) that sits at the edge of your cluster. It is the "Front Door."

**Analogy:**
*   **NodePort:** Giving every employee in a building their own personal side door.
*   **Ingress:** A central Hotel Receptionist. You walk in the main door, say "I want to see the API team," and the receptionist gives you a badge and points you to the elevators.

---

## 2. Deep Dive: What is a Reverse Proxy?

To understand Ingress, you must understand the **Reverse Proxy**. Nginx (which powers our Ingress) is the world's most popular Reverse Proxy.

### Direct Connection (No Proxy)
The user talks directly to the server. If the server moves or crashes, the user gets a connection error.
```ascii
[ User ] ──────────────▶ [ Application Server ]
```

### Reverse Proxy (The Middleman)
The user talks to the Proxy. The Proxy talks to the Server.
```ascii
[ User ] ──(1) Request──▶ [ Nginx Proxy ] ──(2) Forward──▶ [ Server A ]
                          [   (Public)  ] ──(3) Forward──▶ [ Server B ]
```

**Why Big Companies use this:**
1.  **Security:** The user never touches the internal servers. The Proxy can block attacks (WAF).
2.  **SSL Termination:** The heavy math of decrypting HTTPS happens at the Proxy (Hardware accelerated), saving CPU on the App Servers.
3.  **Routing:** The Proxy can say: "Traffic for `/video` goes to Server A, traffic for `/chat` goes to Server B."

---

## 3. Architecture: The Traffic Flow

Here is exactly what happens when you type `curl http://async.local/analyze`:

```ascii
      1. DNS Resolution (/etc/hosts)
      "async.local = 192.168.49.2"
                │
                ▼
      2. HTTP Request (Host: async.local)
                │
      [ Minikube VM Interface (Port 80) ]
                │
                ▼
    ┌───────────────────────────────────┐
    │  Nginx Ingress Controller (Pod)   │ ◀── The "Brain"
    │  (Reads 'Ingress' YAML rules)     │
    └───────────┬───────────────────────┘
                │
                │ 3. Matches Host "async.local"
                │ 4. Looks up Service "api-service"
                │
                ▼
    ┌───────────────────────────────────┐
    │      Service: api-service         │ ◀── Internal DNS
    └───────────┬───────────────────────┘
                │
                │ 5. Selects a healthy Pod (Round Robin)
                │
                ▼
      ┌───────────────────────┐
      │   Pod: api-xv9z2      │ ◀── Your Code
      └───────────────────────┘
```

---

## 4. Implementation Details

### The Setup
1.  **Enable Controller:** `minikube addons enable ingress`.
    *   *Why?* K8s doesn't have a load balancer code built-in. It needs a plugin (Controller) to actually do the work. We used **Nginx**.
2.  **The Rule (YAML):** We told K8s: "If Host is `async.local`, send to `api-service:8000`".

### The DNS Hack (`/etc/hosts`)
Since we don't own the domain `async.local` on the real internet, we "spoofed" it on our laptop.
*   **File:** `/etc/hosts`
*   **Entry:** `192.168.49.2 async.local`
*   **Result:** When our browser asks "Where is async.local?", our OS lies and points to Minikube.

---

## 5. Production Alternatives (Beyond Minikube)

You asked: *"What do big companies use?"*

### 1. Cloud Load Balancers (AWS/GCP/Azure)
If you run this on AWS EKS, you don't use Nginx as the entry point. You use an **Application Load Balancer (ALB)**.
*   **Tool:** `AWS Load Balancer Controller`.
*   **How it works:** When you create an Ingress YAML, AWS automatically spins up a real physical/virtual Load Balancer outside the cluster.

### 2. Service Mesh (Istio / Linkerd)
For massive scale (Netflix/Uber), Nginx isn't enough. They use **Istio**.
*   **Ingress Gateway:** A super-powered Envoy proxy that handles 100k+ requests/second.
*   **Features:** Canary Deployments ("Send 1% of traffic to v2"), Mutual TLS (mTLS), Circuit Breaking.

### 3. API Gateways (Kong / Apigee)
If you are selling an API (like Stripe or Twilio), you need to charge money and issue API Keys.
*   **Ingress:** Just routes traffic.
*   **Gateway:** Handles Billing, Rate Limiting ("100 req/min"), and Auth.

---

## 6. Troubleshooting Log
We encountered two distinct errors during this phase:

1.  **FastAPI 404 (`{"detail": "Not Found"}`):**
    *   **Cause:** We had a rewrite rule (`rewrite-target: /`) that stripped the URL path. Requesting `/analyze` resulted in the container receiving `/`.
    *   **Fix:** Removed the rewrite annotation to pass the full path.

2.  **Missing Root Route:**
    *   **Cause:** `curl http://async.local/` returned 404 because our Python code was missing the `@app.get("/")` function.
    *   **Fix:** Added the code, rebuilt the image (`v3`), and performed a Rolling Update.

---

### ✅ Phase 1 Complete
We now have professional networking. No more port numbers.

*   **Next Phase:** **Templating (Helm)**. We will stop copying and pasting YAML files and build a "One-Click Deploy" package.