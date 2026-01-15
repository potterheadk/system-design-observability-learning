import requests
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_client import get_llm_client

app = FastAPI()

# 1. Configuration
OBSERVABILITY_API_URL = os.getenv("OBSERVABILITY_API_URL", "http://observability-api:8000/graphql")
llm = get_llm_client()

# 2. The Tool: Function to query your system
def fetch_system_health(service_name: str):
    query = """
    query {
      getServiceHealth(serviceName: "%s") {
        serviceName
        status
        errorRate
        requestRate
      }
    }
    """ % service_name
    
    try:
        response = requests.post(OBSERVABILITY_API_URL, json={'query': query})
        if response.status_code == 200:
            return response.json()
        return {"error": "Failed to contact Observability API"}
    except Exception as e:
        return {"error": str(e)}

# 3. The API Endpoint
class AnalysisRequest(BaseModel):
    query: str # e.g., "Why is service-b failing?"

@app.post("/analyze")
def analyze_incident(request: AnalysisRequest):
    user_query = request.query.lower()
    
    # --- STEP 1: Determine Context (Simple Routing) ---
    # Real agents use "Function Calling", but we will write explicit logic first to learn.
    target_service = "service-b" # Defaulting to B for this demo
    if "service-a" in user_query:
        target_service = "service-a"
        
    # --- STEP 2: Gather Evidence (Tool Use) ---
    print(f"🕵️ Agent gathering evidence for {target_service}...")
    health_data = fetch_system_health(target_service)
    
    # --- STEP 3: Construct Prompt ---
    # We give the AI the data we found.
    prompt = f"""
    You are a Senior Site Reliability Engineer (SRE).
    Analyze the following system status and explain it to a junior engineer.
    
    User Query: "{request.query}"
    
    Current System Telemetry:
    {health_data}
    
    Instructions:
    1. State the current status (HEALTHY, DEGRADED, DOWN).
    2. Cite the Error Rate as evidence.
    3. Suggest a potential cause (e.g., if error rate is 50%, suggest a major outage or misconfiguration. If 10%, suggest a bug).
    4. Keep it professional and concise.
    """
    
    # --- STEP 4: Ask LLM ---
    analysis = llm.generate(prompt)
    
    return {
        "target_service": target_service,
        "raw_data": health_data,
        "ai_analysis": analysis
    }