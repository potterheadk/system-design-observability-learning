# 📦 Phase 2: Templating (Helm)

**Status:** Completed
**Technology:** Helm (The Kubernetes Package Manager)
**Goal:** Stop copying/pasting YAML files. Create a reusable "Chart" that can deploy our entire stack (API, Worker, Redis, Ingress) with one command.

## 1. The Core Concept: Infrastructure as Code (Templates)

### The Problem: Hardcoded YAML
In Phase 1, we had raw YAML files:
```yaml
replicas: 1
image: my-api:v3
```
If we wanted to deploy to **Production** with 10 replicas, we had to duplicate the file and manually edit it to `replicas: 10`. This leads to "Configuration Drift" (Dev and Prod becoming different by accident).

### The Solution: Helm Templates
Helm allows us to replace values with variables:
```yaml
replicas: {{ .Values.api.replicas }}
image: {{ .Values.api.image.repository }}:{{ .Values.api.image.tag }}
```

Now, the logic (YAML structure) is separated from the configuration (`values.yaml`).

## 2. Architecture: The Helm Chart
We created a chart named `async-stack`.

```ascii
[ async-stack/ ]
      │
      ├── Chart.yaml       (Metadata: version 0.1.0)
      ├── values.yaml      (Config: replicas=1, host=async.local)
      │
      └── templates/       (The Blueprints)
            ├── api.yaml
            ├── worker.yaml
            ├── redis.yaml
            └── ingress.yaml
```

## 3. The Deployment Workflow

### Old Way (Imperative)
1. `kubectl apply -f redis.yaml`
2. `kubectl apply -f api.yaml`
3. `kubectl apply -f worker.yaml`
4. *Oops, I forgot to update the image tag in worker.yaml*

### New Way (Declarative)
1. Edit `values.yaml` (Change tag to `v4`).
2. `helm upgrade async-app ./async-stack`
3. Helm calculates the "Diff" and applies changes automatically.

## 4. Key Engineering Challenges

### Challenge: Resource Ownership
**Error:** `Service "api-service" exists and cannot be imported`.
**Cause:** We tried to install a Helm chart on top of resources we created manually via `kubectl apply`. Helm refused to touch them to prevent conflicts.
**Fix:** We had to `kubectl delete` the old manual resources (Deployments, Services, and PVCs) to give Helm a clean slate.

### Challenge: Persistent Volumes
**Observation:** Even after deleting Deployments, the PVC (`redis-data-claim`) remained. Helm failed to install because the PVC already existed.
**Fix:** We manually deleted the PVC to allow Helm to create it fresh. In a real production migration, we would use the `import` flag to keep the data, but for this lab, a clean wipe was safer.

## 5. Commands Reference

| Action | Command |
| :--- | :--- |
| **Create Chart** | `helm create my-chart` |
| **Dry Run** | `helm install test ./chart --debug --dry-run` |
| **Install** | `helm install my-release ./chart` |
| **Upgrade** | `helm upgrade my-release ./chart` |
| **List Releases** | `helm list` |
| **Uninstall** | `helm uninstall my-release` |

---

### ✅ Phase 2 Complete
We have a "One-Click Deploy" system locally.

**Next Phase:** **GitOps (ArgoCD)**.
Instead of running `helm upgrade` manually from our laptop, we will push code to Git, and a robot inside the cluster (ArgoCD) will detect the change and upgrade the cluster for us.
```

**Are you ready for Phase 3 (ArgoCD & GitOps)?** This is the final and most advanced step.