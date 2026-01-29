FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir psutil && \
    apt-get update && \
    apt-get install -y stress-ng && \
    rm -rf /var/lib/apt/lists/*

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Run entrypoint
CMD ["./entrypoint.sh"]
