import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:window_manager/window_manager.dart';

/// Whether Sado runs as the computer companion rather than the phone app.
final isDesktopProvider = Provider<bool>((ref) => DesktopHost.supported);

/// The one window Sado lives in on a computer, in its three shapes: hidden in
/// the tray, a slim voice bar while talking, or the full conversation.
abstract final class DesktopHost {
  static const fullSize = Size(420, 680);
  static const compactSize = Size(420, 76);
  static const compactAskingSize = Size(420, 176);

  // Widget tests run on a developer's Windows machine but stand for the phone
  // app, which has no window to manage.
  static bool get supported =>
      !kIsWeb &&
      Platform.isWindows &&
      !Platform.environment.containsKey('FLUTTER_TEST');

  /// Sets the window up hidden: Sado starts in the tray and only appears
  /// when called.
  static Future<void> prepare() async {
    await windowManager.ensureInitialized();
    const options = WindowOptions(
      size: compactSize,
      title: 'Sado',
      skipTaskbar: true,
      alwaysOnTop: true,
      titleBarStyle: TitleBarStyle.hidden,
      backgroundColor: Colors.transparent,
    );
    await windowManager.waitUntilReadyToShow(options, () async {
      // Closing hides Sado to the tray; it keeps listening for the hotkey.
      await windowManager.setPreventClose(true);
    });
  }

  /// The slim voice bar, shown without taking focus from the app the user
  /// is working in.
  static Future<void> showCompact({bool asking = false}) async {
    await windowManager.setMinimumSize(compactSize);
    await windowManager.setSize(asking ? compactAskingSize : compactSize);
    await windowManager.setAlignment(Alignment.bottomCenter);
    await windowManager.show(inactive: true);
  }

  static Future<void> showFull() async {
    await windowManager.setMinimumSize(fullSize);
    await windowManager.setSize(fullSize);
    await windowManager.setAlignment(Alignment.bottomRight);
    await windowManager.show();
    await windowManager.focus();
  }

  static Future<void> hide() => windowManager.hide();

  static Future<void> quit() async {
    await windowManager.setPreventClose(false);
    await windowManager.close();
  }
}
