@echo off
REM AI Sales Training Platform - Streamlit Frontend Launcher (Windows)

echo 🎯 AI Sales Training Platform
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
    echo.
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📚 Installing dependencies...
pip install -q -r requirements.txt
echo ✅ Dependencies installed
echo.

REM Check backend (simple check)
echo 🔍 Checking backend connection...
echo ⚠️  Please ensure your FastAPI backend is running on http://localhost:8000
echo    Start backend: cd ai-backend ^&^& uvicorn app.main:app --reload
echo.

REM Start Streamlit
echo 🚀 Starting Streamlit application...
echo ================================
streamlit run streamlit_app.py

pause