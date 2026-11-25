# Krishok AI API

FastAPI inference service that shares the mobile app's `POST /v1/rice/detect` contract.
It loads the repository's rice MobileNetV3 checkpoint only when its SHA-256 matches
the approved artifact recorded in `app/krishok_ai_app/ai_integration_plan.md`.
If the checkpoint or ML runtime is unavailable, `/health` reports `modelReady: false`
and prediction requests return HTTP 503. The service never generates placeholder results.

## Run locally

Use Python 3.11 or 3.12 in a virtual environment. Install the PyTorch and torchvision
wheels appropriate for your CPU/GPU from the official PyTorch install selector, then:

```sh
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Set `KRISHOK_MODEL_PATH` if the checkpoint is stored elsewhere, and
`KRISHOK_CORS_ORIGINS` to a comma-separated list of trusted website origins.
The default upload limit is 10 MB. Supported types are JPG, PNG, and WebP.
Open `http://localhost:8000/docs` for the interactive API description.

For the mobile app, set `EXPO_PUBLIC_API_URL` to a host reachable from the device
before starting Expo; `localhost` on a physical phone points to the phone itself.
