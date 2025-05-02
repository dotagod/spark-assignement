#!/bin/bash

# Start the FastAPI server in the background
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Store the PID of the server
SERVER_PID=$!

# Wait for the server to start
echo "Waiting for server to start..."
sleep 5

# Generate and upload dummy data
python generate_dummy_data.py

# Keep the server running in the foreground
wait $SERVER_PID
