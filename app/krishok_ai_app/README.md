# Krishok AI

Early React Native foundation for rice leaf disease information and future disease checks.

## Current status

- Expo SDK 58, React Native 0.88, TypeScript, Expo Router, and Expo Development Builds.
- Bangla and English UI with Hind Siliguri font support.
- Dashboard, scanner, camera, gallery, result, disease guide, history, and settings screens.
- SQLite-backed preferences and detection history repositories.
- Detection interfaces and a native LiteRT adapter path are prepared.
- No model is bundled and no prediction is fabricated. AI detection remains unavailable until a local verified model, device-tested preprocessing, and native inference are configured.
- Camera live detection sends a low-resolution still frame to the online API after each inference completes, then displays the current rice class and confidence. Configure `EXPO_PUBLIC_API_URL` in `.env.local` before starting Expo; a physical device needs a reachable HTTPS API URL or your computer's LAN IP, not `localhost`.
- Still-photo AI checks and camera live detection use the same online model endpoint. Offline on-device model inference remains unavailable until a verified model is bundled and device-tested.

## Website and backend

- React website: [`website/README.md`](../../website/README.md)
- FastAPI inference backend: [`backend/README.md`](../../backend/README.md)
- The backend serves the approved rice model only when its checksum and runtime dependencies are available. It does not provide placeholder predictions.

## Start

See [setup_guide.md](setup_guide.md). Use an Android or iOS development build; Expo Go does not include the configured TFLite native module.

```sh
npm install
npm run start
```

## Architecture and AI

- [architecture.md](architecture.md)
- [ai_integration_plan.md](ai_integration_plan.md)
- [dependency_report.md](dependency_report.md)
- [test_report.md](test_report.md)
