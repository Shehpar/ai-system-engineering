# Use an official Python image
#FROM python:3.9-slim
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (we will create this next)
COPY requirements.txt .

# Install necessary Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Run the detection script by default
CMD ["python", "src/detect_anomaly.py"]