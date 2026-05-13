@echo off
echo Starting TeamFlow Backend...
cd backend
start cmd /k "if not exist venv (python -m venv venv) & call venv\Scripts\activate & pip install -r requirements.txt & python run.py"
echo Starting TeamFlow Frontend...
cd ../frontend
start cmd /k "npm install && npm run dev"
echo System starting, please check the new windows.
