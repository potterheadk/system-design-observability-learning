import redis
import time
import os
import json
import sys

# 1. Setup Connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

STREAM_KEY = "job_queue"
CONSUMER_GROUP = "ai_processors"
CONSUMER_NAME = f"worker-{os.getenv('HOSTNAME', 'local')}"

# ✅ ROBUST FUNCTION: Ensure Group Exists
def ensure_consumer_group():
    """
    Tries to create the consumer group. 
    If it already exists, it ignores the error.
    """
    try:
        r.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
        print(f"🔧 Created Consumer Group: {CONSUMER_GROUP}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            # This is fine, it means it already exists
            pass
        else:
            print(f"⚠️ Unexpected Redis Error during setup: {e}")

print(f"👷 Robust Worker {CONSUMER_NAME} started.")

# Initial Setup
ensure_consumer_group()

while True:
    try:
        # 2. Read from Stream
        entries = r.xreadgroup(CONSUMER_GROUP, CONSUMER_NAME, {STREAM_KEY: ">"}, count=1, block=5000)
        
        if not entries:
            continue

        stream, messages = entries[0]
        message_id, job_data = messages[0]
        
        job_id = job_data.get("job_id")
        text = job_data.get("text")
        
        # --- PROCESSING LOGIC (Same as before) ---
        r.hset(f"job:{job_id}", mapping={"status": "processing"})
        print(f"🔄 Job {job_id}: Processing...")
        
        try:
            if "die" in text: raise ValueError("Simulated Crash")
            time.sleep(5)
            
            result_data = {"job_id": job_id, "status": "completed", "result": "Success"}
            r.hset(f"job:{job_id}", mapping=result_data)
            r.publish(f"job_updates:{job_id}", json.dumps(result_data))
            print(f"✅ Job {job_id}: Success")
            
        except Exception as e:
            error_data = {"job_id": job_id, "status": "failed", "error": str(e)}
            r.hset(f"job:{job_id}", mapping=error_data)
            r.publish(f"job_updates:{job_id}", json.dumps(error_data))
            print(f"❌ Job {job_id} Failed")
            
        r.xack(STREAM_KEY, CONSUMER_GROUP, message_id)

    except redis.exceptions.ResponseError as e:
        # ✅ THE FIX: Catch NOGROUP and Auto-Heal
        if "NOGROUP" in str(e):
            print(f"🚨 Redis Group missing! Recreating...")
            ensure_consumer_group()
            time.sleep(1) # Breathe
        else:
            print(f"🔥 Redis Error: {e}")
            time.sleep(5)

    except redis.exceptions.ConnectionError:
        print("🔌 Connection to Redis lost. Retrying...")
        time.sleep(5)
        
    except Exception as e:
        print(f"💥 Unknown Error: {e}")
        time.sleep(1)