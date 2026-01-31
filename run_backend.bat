@echo off
cd /d "%~dp0"
echo AgriSmart Backend - keep this window open.
echo.
echo Working directory: %CD%
set PYTHONPATH=%CD%
echo PYTHONPATH=%PYTHONPATH%
echo.
echo Starting API...
echo.
echo   Open in browser:  http://localhost:8000
echo   Health check:      http://localhost:8000/health
echo   (Do NOT use http://0.0.0.0:8000 - use localhost)
echo.
echo.
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
if errorlevel 1 (
  echo.
  echo Backend failed to start. Check errors above.
  echo Make sure you ran: pip install -r backend\api\requirements.txt
)
pause
