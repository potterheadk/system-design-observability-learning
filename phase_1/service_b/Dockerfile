FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
# CMD will be overridden in compose, but good practice
CMD [uvicorn, main:app, --host, 0.0.0.0, --port, 8000] service_b/Dockerfile
