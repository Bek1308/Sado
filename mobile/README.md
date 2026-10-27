# Sado mobile

Flutter app. Layout and rules: [Engineering principles](../docs/ENGINEERING.md).

## Run

Start the [server](../server/README.md) first, then:

```bash
flutter run
```

The app talks to `http://10.0.2.2:8000` (the host machine from the Android emulator).
On a real device, pass the computer's address on the local network:

```bash
flutter run --dart-define=SADO_API_URL=http://192.168.1.5:8000
```

## Check

```bash
dart format --set-exit-if-changed lib test
dart analyze
flutter test
```
