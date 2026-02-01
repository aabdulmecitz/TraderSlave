FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY dumb_datas/ ./dumb_datas/
COPY test_engine.py .

# Create directories
RUN mkdir -p /app/output /app/product_datas

# Default: show help
CMD ["python", "-m", "src.main", "--help"]
