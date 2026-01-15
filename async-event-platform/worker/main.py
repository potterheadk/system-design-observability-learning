import redis
import time
import os
import json
import random

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

STREAM_KEY = "job_queue"
CONSUMER_GROUP = "ai_processors"
CONSUMER_NAME = "worker-1"

# Create Consumer Group if not exists
try:
    r.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
except redis.exceptions.ResponseError:
    pass

print(f"👷 Robust Worker {CONSUMER_NAME} started.")

while True:
    try:
        # 1. Read from Stream
        entries = r.xreadgroup(CONSUMER_GROUP, CONSUMER_NAME, {STREAM_KEY: ">"}, count=1, block=5000)
        if not entries:
            continue

        stream, messages = entries[0]
        message_id, job_data = messages[0]
        
        job_id = job_data.get("job_id")
        text = job_data.get("text")
        
        # ✅ STEP 1: Mark as PROCESSING
        r.hset(f"job:{job_id}", mapping={"status": "processing"})
        print(f"🔄 Job {job_id}: Processing started...")

        try:
            # ✅ STEP 2: The Dangerous Work
            
            # SIMULATE POISON PILL: If text contains "die", crash the logic
            if "die" in text:
                raise ValueError("Simulated AI Crash!")
            
            # Simulate work
            time.sleep(12) 
            
            # ✅ STEP 3: Success
            r.hset(f"job:{job_id}", mapping={
                "status": "completed",
                "result": "AI Analysis Success"
            })
            print(f"✅ Job {job_id}: Success")
            
        except Exception as e:
            # ✅ STEP 4: Failure Handling
            print(f"❌ Job {job_id} Failed: {str(e)}")
            r.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "error": str(e)
            })
        
        # Always Ack (even if failed, so we don't retry it infinitely in this loop)
        r.xack(STREAM_KEY, CONSUMER_GROUP, message_id)

    except Exception as e:
        print(f"🔥 Critical Worker Error: {str(e)}")
        time.sleep(1)