# Setup guide

## Requirements

- Node.js 22.13 or newer; this project was prepared with Node 26.7.0 and npm 11.19.0.
- Android: Android Studio, Android SDK and a configured emulator or physical device for native builds.
- iOS: macOS with Xcode 26.4 or newer for local builds, or an EAS development build. This repository was inspected on Windows, so iOS native compilation was not available here.
- A development build is required because `react-native-fast-tflite` and Nitro Modules contain native code.

## Install and start Metro

```powershell
cd app/krishok_ai_app
npm install
npm run start
```

## Build a development client

Local Android build:

```powershell
npm run android
```

Local iOS build (macOS only):

```sh
npm run ios
```

EAS development build:

```sh
npx eas-cli build --profile development --platform android
npx eas-cli build --profile development --platform ios
```

After adding or changing native modules, rebuild the development client. Android and iOS native projects are generated through Expo Continuous Native Generation; do not hand-edit generated `android/` or `ios/` directories.

## Check dependencies and source

```sh
npx expo install --check
npx expo-doctor
npm run typecheck
npm test
npx expo lint
```

## AI configuration

No model artifact or server URL is configured by default. `extra.offlineModelUri` and `extra.onlineApiBaseUrl` are `null`. See [ai_integration_plan.md](ai_integration_plan.md) before supplying either value.
