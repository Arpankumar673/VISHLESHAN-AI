# Vishleshan AI — FastAPI Backend

Enterprise backend for Vishleshan AI Company Intelligence & Verification Platform.

## Requirements
* Python 3.10+
* Dependencies: `pip install -r requirements.txt`

## Running Locally

1. Create or verify `.env`:
```bash
cp .env.example .env
```

2. Run tests:
```bash
python -m pytest -v
```

3. Run FastAPI application:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

API documentation will be available at:
* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`
