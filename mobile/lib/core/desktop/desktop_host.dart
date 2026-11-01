import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:window_manager/window_manager.dart';

/// Whether Sado runs as the computer companion rather than the phone app.
final isDesktopProvider = Provider<bool>((ref) => DesktopHost.supported);

/// The small always-on-top window Sado lives in on a computer.
abstract final class DesktopHost {
  static const size = Size(420, 680);

  // Widget tests run on a developer's Windows machine but stand for the phone
  // app, which has no window to manage.
  static bool get supported =>
      !kIsWeb &&
      Platform.isWindows &&
      !Platform.environment.containsKey('FLUTTER_TEST');

  /// Sets the window up before the first frame, so it never flashes at the
  /// wrong size or place.
  static Future<void> prepare() async {
    await windowManager.ensureInitialized();
    const options = WindowOptions(
      size: size,
      minimumSize: size,
      title: 'Sado',
      skipTaskbar: true,
      alwaysOnTop: true,
      titleBarStyle: TitleBarStyle.hidden,
    );
    await windowManager.waitUntilReadyToShow(options, () async {
      // Closing hides Sado to the tray; it keeps listening for the hotkey.
      await windowManager.setPreventClose(true);
      await windowManager.setAlignment(Alignment.bottomRight);
      await windowManager.show();
    });
  }

  static Future<void> reveal() async {
    await windowManager.show();
    await windowManager.focus();
  }

  static Future<void> hide() => windowManager.hide();

  static Future<void> quit() async {
    await windowManager.setPreventClose(false);
    await windowManager.close();
  }
}
