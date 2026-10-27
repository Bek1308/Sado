abstract final class AppConfig {
  static const apiBaseUrl = String.fromEnvironment(
    'SADO_API_URL',
    // The Android emulator reaches the host machine through 10.0.2.2.
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const connectTimeout = Duration(seconds: 5);
  static const receiveTimeout = Duration(seconds: 30);
}
