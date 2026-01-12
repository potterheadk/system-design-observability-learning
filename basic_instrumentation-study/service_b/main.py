import time
import random
import structlog
import logging
import sys
from fastapi import FastAPI, Response, Request
from prometheus_fastapi_instrumentator import Instrumentator

# --- FIX: Enable INFO logs to stdout ---
logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

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

# 2. Middleware: Extract Request ID from Headers
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id", "unknown")
    log = logger.bind(request_id=request_id)
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # This was being silenced before!
    log.info(
        "request_finished",
        path=request.url.path,
        status=response.status_code,
        duration=process_time
    )
    return response

@app.get("/data")
def get_data():
    time.sleep(random.uniform(0.1, 0.3))
    if random.random() < 0.1:
        return Response(status_code=500, content="Internal Worker Error")
    return {"result": "processed_data", "worker_id": "b-node-1"}