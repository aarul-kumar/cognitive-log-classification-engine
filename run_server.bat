@echo off
cd /d C:\Users\aarul\classification-logs
call .\myenv310\Scripts\activate.bat
uvicorn server:app --reload --host 127.0.0.1 --port 8000
