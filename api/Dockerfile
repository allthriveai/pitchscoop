FROM python:3.11-slim

WORKDIR /app

# Install system dependencies first (rarely change)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel for better dependency resolution
RUN pip install --upgrade pip setuptools wheel

# Copy and install requirements (cache this layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

# Copy source code last (changes frequently)
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
