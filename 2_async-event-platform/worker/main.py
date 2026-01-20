import redis
import time
import os
import json
import random

# ... (Connection setup remains the same) ...
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

STREAM_KEY = "job_queue"
CONSUMER_GROUP = "ai_processors"
CONSUMER_NAME = "worker-1"

# ... (Group creation remains the same) ...
print(f"📣 Chatty Worker {CONSUMER_NAME} started.")

while True:
    try:
        # ... (Reading from stream remains the same) ...
        entries = r.xreadgroup(CONSUMER_GROUP, CONSUMER_NAME, {STREAM_KEY: ">"}, count=1, block=5000)
        if not entries:
            continue

        stream, messages = entries[0]
        message_id, job_data = messages[0]
        
        job_id = job_data.get("job_id")
        text = job_data.get("text")
        
        # Mark processing
        r.hset(f"job:{job_id}", mapping={"status": "processing"})

        try:
            # Simulate Work
            if "die" in text:
                raise ValueError("Simulated AI Crash!")
            
            time.sleep(5) # 😴 Nap time
            
            # --- SUCCESS ---
            result_data = {
                "job_id": job_id,
                "status": "completed",
                "result": "AI Analysis Success"
            }
            
            # 1. Save to DB (Hash)
            r.hset(f"job:{job_id}", mapping=result_data)
            
            # 📢 2. PUBLISH THE NEWS! (The Megaphone)
            # Channel Name: "job_updates:{job_id}"
            # Message: JSON string of the result
            r.publish(f"job_updates:{job_id}", json.dumps(result_data))
            
            print(f"✅ Job {job_id}: Success & Published")
            
        except Exception as e:
            # --- FAILURE ---
            error_data = {
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            }
            r.hset(f"job:{job_id}", mapping=error_data)
            
            # 📢 PUBLISH THE BAD NEWS TOO!
            r.publish(f"job_updates:{job_id}", json.dumps(error_data))
            
            print(f"❌ Job {job_id} Failed & Published")
        
        r.xack(STREAM_KEY, CONSUMER_GROUP, message_id)

    except Exception as e:
        print(f"🔥 Critical Worker Error: {str(e)}")
        time.sleep(1)