@echo off
cd /d "%~dp0"
echo AgriSmart: starting backend and frontend...
start "AgriSmart Backend" cmd /k "set PYTHONPATH=%CD% && python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul
start "AgriSmart Frontend" cmd /k "streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8501
pause
