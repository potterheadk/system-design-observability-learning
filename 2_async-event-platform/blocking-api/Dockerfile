FROM python:3.9-slim
WORKDIR /app

# 1. Copy the requirements file first
COPY requirements.txt .

# 2. NOW install (because the file exists)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Then copy the rest of the code
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]