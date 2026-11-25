# Krishok AI website

React + Vite website for rice leaf disease information and image uploads.

```sh
npm install
npm run dev
```

Set `VITE_API_URL` (see `.env.example`) when the API is not at `http://localhost:8000`.
The website calls `POST /v1/rice/detect` and displays a clear error if the service is unavailable.
