import strawberry
import os
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from prometheus_api_client import PrometheusConnect

# 1. Connect to Prometheus
# We use the docker network name "prometheus"
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# 2. Define the Data Structure (The "Shape" of the answer)
@strawberry.type
class ServiceHealth:
    service_name: str
    request_rate: float  # Requests per second
    error_rate: float    # Percent of requests failing
    status: str          # HEALTHY, DEGRADED, or DOWN

# 3. Define the Logic (The "Resolver")
@strawberry.type
class Query:
    @strawberry.field
    def get_service_health(self, service_name: str) -> ServiceHealth:
        # --- A. Get Request Rate (Requests/sec) ---
        # PromQL: sum(rate(http_requests_total{job="service_name"}[2m]))
        rate_query = f'sum(rate(http_requests_total{{job="{service_name}"}}[2m]))'
        rate_data = prom.custom_query(query=rate_query)
        
        req_rate = 0.0
        if rate_data and len(rate_data) > 0:
            req_rate = float(rate_data[0]['value'][1])

        # --- B. Get Error Rate (Errors/sec) ---
        # PromQL: sum(rate(http_requests_total{job="service_name", status=~"5.."}[2m]))
        error_query = f'sum(rate(http_requests_total{{job="{service_name}", status=~"5.."}}[2m]))'
        error_data = prom.custom_query(query=error_query)
        
        err_rate = 0.0
        if error_data and len(error_data) > 0:
            err_rate = float(error_data[0]['value'][1])

        # --- C. Calculate Percentage ---
        error_percent = 0.0
        if req_rate > 0:
            error_percent = (err_rate / req_rate) * 100

        # --- D. Determine Status ---
        status = "HEALTHY"
        if error_percent > 1: # If > 1% errors, it's Degraded
            status = "DEGRADED"
        if error_percent > 20: # If > 20% errors, it's Down
            status = "DOWN"

        return ServiceHealth(
            service_name=service_name,
            request_rate=round(req_rate, 2),
            error_rate=round(error_percent, 2),
            status=status
        )

# 4. Create the App
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")