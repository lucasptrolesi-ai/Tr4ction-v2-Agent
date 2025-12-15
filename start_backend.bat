@echo off
cd /d C:\Users\Micro\Desktop\Tr4ction_Agent_V2\backend
C:\Users\Micro\Desktop\Tr4ction_Agent_V2\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
pause
