abstract final class AppConfig {
  static const apiBaseUrl = String.fromEnvironment(
    'SADO_API_URL',
    // The Android emulator reaches the host machine through 10.0.2.2.
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// Where Sado turns when the main server is away, e.g. the laptop that
  /// hosts it is closed. Empty means there is no backup.
  static const backupApiBaseUrl = String.fromEnvironment('SADO_BACKUP_API_URL');

  /// The Firebase project's web client: Google signs sign-in tokens for it.
  /// It is public by design and identifies the app, not a person.
  static const googleWebClientId = String.fromEnvironment(
    'SADO_GOOGLE_WEB_CLIENT_ID',
    defaultValue:
        '618143439495-4po12a5k5gvqmvulcovsdmprf8isd1n5'
        '.apps.googleusercontent.com',
  );

  /// Proves this build may drive the computer Sado runs on. Only the desktop
  /// app is built with it, so a phone can never control the computer.
  static const desktopToken = String.fromEnvironment('SADO_DESKTOP_TOKEN');

  static const connectTimeout = Duration(seconds: 10);
  // Thinking and speaking a long answer on a local GPU can take a while.
  static const receiveTimeout = Duration(seconds: 120);
}
