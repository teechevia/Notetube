to run by terminal
write :


python -m venv venv
.\venv\Scriipts\Activate
pip install -r requirements.txt
cd backend
python -m uvicorn main:app --reload --port 8000