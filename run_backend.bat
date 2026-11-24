@echo off
echo ========================================================
echo  Starting CarePoint Health AI Backend on Port 8000
echo ========================================================
set PYTHONPATH=backend
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
pause
