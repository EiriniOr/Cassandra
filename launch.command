#!/bin/bash
# Double-click this file in Finder to launch Cassandra locally.
# Opens http://localhost:8000 in your browser.

set -e
cd "$(dirname "$0")"

# Activate venv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install deps if missing
if ! python -c "import fastapi, anthropic, uvicorn, dotenv" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Verify .env exists
if [ ! -f ".env" ]; then
    echo "❌ No .env file. Create one with ANTHROPIC_API_KEY (see .env.example)."
    read -p "Press enter to exit..."
    exit 1
fi

# Open browser after a short delay so the server is up
( sleep 1.2; open "http://localhost:8000" ) &

# Run the server (foreground, Ctrl+C to quit)
python server.py
