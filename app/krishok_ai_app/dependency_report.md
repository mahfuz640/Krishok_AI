# Dependency report

## Selected stack

| Area               | Package                                               |    Installed version | Notes                                                       |
| ------------------ | ----------------------------------------------------- | -------------------: | ----------------------------------------------------------- |
| Framework          | Expo                                                  |               58.0.x | SDK release line selected by the current Expo tabs template |
| UI runtime         | React Native                                          |               0.88.1 | SDK 58 target                                               |
| Language           | TypeScript                                            |                6.0.x | Strict mode enabled                                         |
| Navigation         | Expo Router                                           |               58.0.x | File routes under `src/app/`                                |
| State              | Zustand                                               |                  5.x | Local preferences and boot hydration                        |
| Localization       | i18next / react-i18next                               |          27.x / 18.x | English and Bangla resources                                |
| Persistence        | expo-sqlite                                           |               58.0.x | SQLite-backed preferences and history                       |
| Camera and gallery | expo-camera / expo-image-picker                       |               58.0.x | Expo SDK-compatible packages                                |
| Native TFLite path | react-native-fast-tflite / react-native-nitro-modules |       3.0.1 / 0.37.x | Config plugin and custom development build required         |
| Tests              | Jest / jest-expo / React Native Testing Library       | 30.x / 58.0.x / 14.x | SDK 58 Jest guidance                                        |

Exact versions and integrity are in `package-lock.json`. Expo SDK packages were selected with `npx expo install`; the final compatibility check is `npx expo install --check`.

## Compatibility notes

- Expo SDK 58 targets React Native 0.88 and requires Node 22.13 or newer. Local Node 26.7.0 satisfies that requirement.
- The TFLite package relies on Nitro Modules and requires a development build. Metro recognizes `.tflite` files, but no model is included in the application bundle.
- Current native module compatibility still requires a real Android and iOS development build; desktop package checks cannot substitute for that build.
- Expo Doctor passed 19 of 20 checks. The remaining React Native Directory warning marks `react-native-fast-tflite` as untested on the New Architecture; device compilation is still required to establish compatibility for this project configuration.
- Expo's camera and image picker use SDK-matched versions. Camera and photo permissions are declared through Expo config plugins.

## Install audit

The initial npm install reported moderate audit findings. Review `npm audit` output before release; no forced dependency upgrades were applied because they can break the Expo SDK version set.
