@echo off
echo ========================================================
echo  Starting CarePoint Health Clinical Dashboard on Port 5173
echo ========================================================
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
pause
