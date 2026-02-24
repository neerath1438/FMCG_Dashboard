@echo off
echo Installing FastAPI dependencies...
cd backend
pip install -r requirements.txt
echo.
echo Dependencies installed!
echo.
echo Starting FastAPI server...
python app.py
