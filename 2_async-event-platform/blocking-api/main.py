import uuid
import os
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

class DocumentRequest(BaseModel):
    text: str

@app.post("/analyze")
def submit_job(request: DocumentRequest):
    job_id = str(uuid.uuid4())
    
    # 1. Initialize State in Redis (So /status knows it exists)
    # We use a Hash Map "job:{id}" to store details
    r.hset(f"job:{job_id}", mapping={
        "status": "queued",
        "submitted_at": str(os.times().elapsed) # Simple timestamp substitute
    })
    
    # 2. Push to Worker Queue
    job_data = {
        "job_id": job_id,
        "text": request.text
    }
    r.xadd("job_queue", job_data)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "info": "Use GET /status/{job_id} to check results"
    }

# ✅ NEW: The Polling Endpoint
@app.get("/status/{job_id}")
def check_status(job_id: str):
    # 1. Fetch data from Redis
    job_key = f"job:{job_id}"
    
    # Check if key exists
    if not r.exists(job_key):
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all fields from the hash
    job_data = r.hgetall(job_key)
    
    return job_data