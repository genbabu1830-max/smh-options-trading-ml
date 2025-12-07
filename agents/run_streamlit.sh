#!/bin/bash
# Run Streamlit App for Recommendation Agent

echo "Starting Streamlit App..."
echo "================================"
echo ""
echo "The app will open in your browser at:"
echo "http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run streamlit
streamlit run streamlit_app.py
