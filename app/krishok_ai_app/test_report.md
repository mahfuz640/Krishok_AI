# Development and test report

## Completed checks

| Check                                                            | Result                                    |
| ---------------------------------------------------------------- | ----------------------------------------- |
| Expo config resolution                                           | Passed                                    |
| Expo SDK package compatibility (`npx expo install --check`)      | Passed; dependencies up to date           |
| TypeScript (`npm run typecheck`)                                 | Passed                                    |
| Unit and component tests (`npm test -- --coverage=false`)        | Passed; 10 suites, 18 tests               |
| ESLint (`npm run lint`)                                          | Passed with 0 errors and 9 warnings       |
| Android JavaScript export (`npx expo export --platform android`) | Passed; 1,398 modules bundled             |
| iOS JavaScript export (`npx expo export --platform ios`)         | Passed; 1,395 modules bundled             |
| Expo Doctor                                                      | 19/20 checks passed; see limitation below |

Tests cover the approved disease class IDs, prediction validation, offline-unavailable behavior, preprocessing normalization, gallery selection and cancellation, SQLite repository operations, preference parameterization, camera permission messaging, startup, home navigation, localization, and result/history empty and error states.

## Open checks and limits

- Expo Doctor reports `react-native-fast-tflite` as “Untested on New Architecture” in React Native Directory metadata. The package uses Nitro Modules and is configured for a custom development build, but it has not been compiled or exercised on a device here.
- No Android SDK/ADB, Java toolchain, EAS CLI, Xcode, or iOS host was available in this Windows environment. Native Android/iOS development builds, camera/gallery hardware permissions, SQLite on-device behavior, and TFLite runtime execution remain unverified.
- The two platform exports validate JavaScript bundling, not native compatibility or application startup on a device.
- No model binary is packaged in this app. No prediction has been generated or written to history by a mock implementation.
- ESLint reports 9 non-blocking warnings, mostly `require()` usage in test mocks plus an i18next import warning.

## Next verification step

Build development clients for Android and iOS, install them on representative devices, verify camera/gallery permission flows and SQLite persistence, then test native model loading and compare outputs against the approved Python/TFLite reference before enabling detection.
