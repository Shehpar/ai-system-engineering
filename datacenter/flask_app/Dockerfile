# Use a slim Linux-based Python image
FROM python:3.9-slim

# Install system dependencies needed for psutil to monitor Linux hardware
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Install Python libraries
RUN pip install --no-cache-dir flask psutil

# Copy your app code into the container
COPY app.py .

# Expose the port the web server runs on
EXPOSE 5000

# Start the Linux Web Server
CMD ["python", "app.py"]
