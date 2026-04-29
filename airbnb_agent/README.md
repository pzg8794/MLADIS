# MLADIS Airbnb Agent

Small Flask scaffold for a deployable booking-agent web app.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Visit `http://localhost:5000`.

## Deployment

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Required environment variable: `OPENAI_API_KEY`
- Health check path: `/healthz`

The app currently returns an agent-ready stub response. Replace `build_agent_reply` in `app.py` when the real booking logic is ready.
