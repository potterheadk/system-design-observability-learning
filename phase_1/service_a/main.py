import requests
import os
import uuid
import structlog
import time
from fastapi import FastAPI, HTTPException, Request
from prometheus_fastapi_instrumentator import Instrumentator

# 1. Configure JSON Logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger()

app = FastAPI()
Instrumentator().instrument(app).expose(app)

SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://localhost:8002")

# 2. Middleware: Generate Request ID
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Create a unique ID for this request
    request_id = str(uuid.uuid4())
    
    # Contextualize the logger (all logs in this scope get the ID)
    log = logger.bind(request_id=request_id)
    
    log.info("request_started", path=request.url.path, method=request.method)
    
    # Store ID in request state so endpoints can use it
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    log.info("request_finished", status=response.status_code, duration=process_time)
    
    # Return ID to user in headers (good for debugging)
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/")
def read_root():
    return {"message": "Service A is alive"}

@app.get("/chain")
def call_chain(request: Request):
    # Retrieve the ID generated in middleware
    req_id = request.state.request_id
    
    headers = {"X-Request-ID": req_id}
    
    try:
        # 3. PASS THE ID downstream to Service B
        resp = requests.get(f"{SERVICE_B_URL}/data", headers=headers, timeout=2)
        
        if resp.status_code >= 500:
            logger.error("upstream_failed", request_id=req_id, upstream_status=resp.status_code)
            raise HTTPException(status_code=502, detail="Upstream Service B Failed")
            
        return {"service_a": "ok", "upstream": resp.json()}
        
    except requests.exceptions.RequestException as e:
        logger.error("upstream_connection_error", request_id=req_id, error=str(e))
        raise HTTPException(status_code=503, detail=f"Connection Error: {str(e)}")