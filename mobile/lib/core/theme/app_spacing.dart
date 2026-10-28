/// One spacing scale for the whole app, so every screen keeps the same rhythm.
abstract final class AppSpacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
  static const xxl = 32.0;
}

abstract final class AppRadius {
  static const sm = 12.0;
  static const md = 16.0;
  static const lg = 24.0;

  /// The corner a chat bubble points from, kept tight so it reads as a tail.
  static const tail = 6.0;
}

abstract final class AppLayout {
  /// Keeps lines readable on tablets and desktop windows.
  static const maxContentWidth = 720.0;
}
