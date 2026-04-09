@echo off
TITLE AI Quant Platform - Startup
CHCP 65001 > nul

echo ==========================================
echo    AI Quant Trading Platform Startup
echo ==========================================
echo.

:: 1. Start Backend
echo [+] Starting Backend (FastAPI)...
start "Backend - FastAPI" cmd /k ".\.venv\Scripts\activate && uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

:: 2. Start Frontend
echo [+] Starting Frontend (Vite)...
cd frontend
start "Frontend - Vite" cmd /k "npm run dev"

echo.
echo ==========================================
echo    System Startup Initiated!
echo    Backend: http://127.0.0.1:8000
echo    Frontend: Check the frontend window (usually http://localhost:5173)
echo ==========================================
echo.
pause
