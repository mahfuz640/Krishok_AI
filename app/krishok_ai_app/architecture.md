# Architecture

The app uses feature-based presentation with domain, data, and core-service boundaries.

```text
src/app/                 Expo Router screens and layouts
src/features/            Camera/gallery flows and screen-focused behavior
src/components/          Shared screen, typography, card, notice, and button components
src/domain/              Approved disease mapping, detection mode, prediction types
src/data/                SQLite initialization, preferences, detection history
src/core/ai/             Detection contracts, preprocessing, online and offline adapters
src/core/localization/   i18next resources and initialization
src/core/store/          Zustand UI preferences and hydration
```

## Boundaries

- Route files compose feature services and reusable UI. Native AI calls are isolated in `core/ai`.
- `DiseaseDetectionService` has online and offline implementations. The current configured service instances return explicit unavailable errors until a real API or device-verified local runtime is supplied.
- `PredictionResult` validates the class ID and confidence range before a prediction can be displayed or stored.
- `ImagePreprocessingService` takes image URIs through a decoder interface. The decoder must return oriented RGB pixels with the model's 232-pixel resize, antialias, and 224-pixel center crop applied before normalization.
- `DetectionHistoryRepository` stores the image URI, timestamp, approved class ID, confidence, and mode. The UI only writes a history entry after a real service returns a validated prediction.
- Preferences and history use separate SQLite tables. Zustand provides responsive UI state and hydrates preferences from SQLite at startup.
- UI strings live in English and Bangla resource files. Hind Siliguri is loaded for Bangla presentation; system fonts are used for English.

## Navigation

Expo Router uses `src/app/`. The tab navigator contains Home, History, and Settings. Scanner, Camera, Gallery, Result, Disease Guide, and Disease Details are stack routes.
