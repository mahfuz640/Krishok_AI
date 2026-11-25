# Deploy Krishok AI on Render

This repository includes a Render Blueprint at render.yaml for the FastAPI inference
API and React website. Render uses the repository root for the API so it can read the
approved model at AI/experiments/MobileNetV3_Rice/best_model.pt; the website builds as
a static Vite site.

## Deploy

1. Push the repository to GitHub.
2. In Render, choose New → Blueprint, connect mahfuz640/Krishok_AI, and select
   the main branch.
3. Review and apply the two services. The API name is krishok-ai-api; the website
   name is krishok-ai-website.
4. Wait for the API health check to report ready, then open the website's onrender.com
   URL. The React build calls the API's public URL over HTTPS.

Render service names must be globally unique. If either default onrender.com hostname
is changed because it is already taken, update VITE_API_URL on the static site and
KRISHOK_CORS_ORIGINS on the API to the actual public website URL, then redeploy both.

## Mobile app

Set EXPO_PUBLIC_API_URL to the API's public HTTPS URL when building the Expo app.
Physical devices cannot use localhost to reach a computer-hosted API.

## Notes

- The API validates the committed model checkpoint's SHA-256 at startup and exposes
  /health and /docs.
- The API uses one worker to keep model memory use predictable. If Render reports an
  out-of-memory restart during inference, upgrade the API service to a 2 GB instance.
- Dataset archives and training data are excluded from Git; the inference checkpoint
  is tracked in the repository.
