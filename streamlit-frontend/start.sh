#!/bin/bash

# AI Sales Training Platform - Streamlit Frontend Launcher

echo "🎯 AI Sales Training Platform"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend not detected on http://localhost:8000"
    echo "   Make sure to start your FastAPI backend:"
    echo "   cd ai-backend && uvicorn app.main:app --reload"
fi
echo ""

# Start Streamlit
echo "🚀 Starting Streamlit application..."
echo "================================"
streamlit run streamlit_app.py