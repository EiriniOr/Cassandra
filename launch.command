#!/bin/bash
# Double-click this file in Finder to launch Cassandra locally.
# Auth still applies — you'll see the login form in the browser.

set -e
cd "$(dirname "$0")"

# Activate venv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install deps if missing
if ! python -c "import streamlit, anthropic, dotenv" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Verify .env exists
if [ ! -f ".env" ]; then
    echo "❌ No .env file. Create one with ANTHROPIC_API_KEY, CASSANDRA_USER, CASSANDRA_PASS."
    echo "   See .env.example."
    read -p "Press enter to exit..."
    exit 1
fi

# Launch — opens browser automatically at localhost:8501
streamlit run app.py
