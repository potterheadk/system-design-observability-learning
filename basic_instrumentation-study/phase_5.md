# 🚀 Phase 5: Zero-Code Auto-Instrumentation

**Status:** Completed  
**Focus:** OpenTelemetry (OTel), Jaeger, Distributed Tracing  
**Engineering Goal:** Eliminate manual logging code and achieve full visibility into microservice interactions automatically.

## 1. The "Before" State (Manual Instrumentation)
In Phases 1-4, we manually instrumented our code.
*   **The Code:** We wrote middleware to generate `UUIDs`.
*   **The Header:** We manually injected `x-request-id` into HTTP headers.
*   **The Logs:** We used `structlog` to print JSON to stdout.
*   **The Pain Point:** If a developer forgot to add the middleware, the trace was broken. We had no visibility into third-party libraries (like database drivers or HTTP clients) without writing more wrappers.

## 2. The "After" State (Zero-Code / Auto-Instrumentation)
We replaced our manual middleware with **OpenTelemetry (OTel) Agents**.

### How it Works (The Magic)
We utilize **Dynamic Instrumentation** (Monkey Patching).
1.  **The Wrapper:** Instead of running `python main.py`, we run `opentelemetry-instrument python main.py`.
2.  **Runtime Patching:** As Python starts, the OTel agent detects installed libraries (like `FastAPI`, `Requests`, `Urllib`).
3.  **Hooks:** It effectively "rewrites" those libraries in memory to send telemetry data whenever they are used.
4.  **Export:** Traces are sent via **gRPC** to our collector (Jaeger).

### Architecture Diagram

```ascii
┌──────────────┐          ┌──────────────┐
│  Service A   │          │  Service B   │
│ (OTel Agent) │          │ (OTel Agent) │
└───┬──────┬───┘          └───┬──────┬───┘
    │      │                  │      │
    │      └──────────────────┼──────┘
    │    (HTTP Request)       │
    ▼                         ▼
  [ gRPC Stream (Port 4317) ]
    │
    ▼
┌───────────────────────────────────────┐
│                Jaeger                 │
│         (Collector & UI)              │
└───────────────────────────────────────┘
```

## 3. Implementation Details

### Docker Configuration
We removed the `command` override in `docker-compose.yml` to allow the `Dockerfile` to control the startup.

**The Command:**
```dockerfile
CMD ["opentelemetry-instrument", \
     "--traces_exporter", "otlp_proto_grpc", \
     "--service_name", "service-a", \
     "--exporter_otlp_endpoint", "http://jaeger:4317", \
     "uvicorn", "main:app", ...]
```

**Why `otlp_proto_grpc`?**
We explicitly chose **gRPC** over HTTP because it is more efficient (binary protocol) and avoids common port configuration issues with the default OTel HTTP exporter.

## 4. Verification (The Waterfall)
In the Jaeger UI (`http://localhost:16686`), we observed:
*   **Spans:** A visual bar for Service A, followed by a child bar for Service B.
*   **Tags:** Automatic capture of metadata (`http.status_code=500`, `http.method=GET`).
*   **Error Propagation:** Visual red error indicators propagating up the stack.

## 5. Key Takeaway
We achieved **Deep Observability** (seeing inside the libraries) without changing a single line of business logic in `main.py`. This is the industry standard for scalable microservices.

