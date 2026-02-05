FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir psutil requests && \
    apt-get update && \
    apt-get install -y stress-ng && \
    rm -rf /var/lib/apt/lists/*

# Copy scripts
COPY entrypoint.sh .
COPY http_load_generator.py .
RUN chmod +x entrypoint.sh

# Run entrypoint
CMD ["./entrypoint.sh"]
