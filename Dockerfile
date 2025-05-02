# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
# Install build tools for python-geohash
RUN apt-get update && apt-get install -y build-essential && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Make the startup script executable
RUN chmod +x /app/startup.sh

# Command to run the startup script
CMD ["/app/startup.sh"]
