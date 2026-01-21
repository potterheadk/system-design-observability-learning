import uuid
import os
import redis
import asyncio # New Friend
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
# 🚨 IMPORTANT: Import the Async Redis client
import redis.asyncio as aioredis 
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware (The "Open Door" Policy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow ALL origins (Browser files, other domains)
    allow_credentials=True,
    allow_methods=["*"],      # Allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],      # Allow all headers
)

# Sync Connection (For submitting jobs - keeping it simple)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r_sync = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

class DocumentRequest(BaseModel):
    text: str

@app.post("/analyze")
def submit_job(request: DocumentRequest):
    job_id = str(uuid.uuid4())
    # ... (Same logic as before) ...
    r_sync.hset(f"job:{job_id}", mapping={"status": "queued"})
    r_sync.xadd("job_queue", {"job_id": job_id, "text": request.text})
    return {"job_id": job_id, "status": "queued"}

# ---------------------------------------------------------
# 📡 THE LIVE WIRE: WebSocket + Redis Pub/Sub
# ---------------------------------------------------------
@app.websocket("/ws/job/{job_id}")
async def job_status_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    # 1. Connect to Redis (Async Mode)
    # We create a specific connection just for this websocket
    r_async = aioredis.from_url(f"redis://{REDIS_HOST}", decode_responses=True)
    pubsub = r_async.pubsub()
    
    channel_name = f"job_updates:{job_id}"
    
    try:
        # 2. Subscribe to the frequency
        await pubsub.subscribe(channel_name)
        print(f"🎧 Client listening on {channel_name}")
        
        # 3. The Infinite Listener Loop
        # We loop until the client disconnects or the job is done
        async for message in pubsub.listen():
            
            # Redis sends a "subscribe" confirmation message first, ignore it
            if message["type"] == "message":
                data = message["data"]
                print(f"⚡ Event Received: {data}")
                
                # 4. Forward the Radio Message to the Browser
                await websocket.send_text(data)
                
                # If job is done, we can close the connection (optional)
                # Let's keep it open for now.

    except WebSocketDisconnect:
        print("❌ Client disconnected")
    except Exception as e:
        print(f"🔥 Error: {e}")
    finally:
        # Cleanup: Turn off the radio
        await pubsub.unsubscribe(channel_name)
        await r_async.close()

@app.get("/status/{job_id}")
def check_status(job_id: str):
    job_key = f"job:{job_id}"
    
    # Use r_sync (the synchronous redis client we defined earlier)
    if not r_sync.exists(job_key):
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = r_sync.hgetall(job_key)
    return job_data