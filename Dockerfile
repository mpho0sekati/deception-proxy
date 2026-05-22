# Use a base image with both Python and Go
FROM golang:1.21-alpine AS go-builder

WORKDIR /app
COPY proxy.go .
RUN go build -o proxy proxy.go

# Use Python base image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Go binary
COPY --from=go-builder /app/proxy /usr/local/bin/proxy

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api.py .
COPY dashboard.py .
COPY setup_env.py .
COPY start.ps1 .
COPY test.ps1 .
COPY run_services.bat .
COPY run_services.ps1 .
COPY safe_run.py .

# Expose ports
EXPOSE 8000 8080 8501

# Default command
CMD ["python", "safe_run.py"]