import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hotkey_manager/hotkey_manager.dart';
import 'package:sado/core/desktop/desktop_host.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:tray_manager/tray_manager.dart';
import 'package:window_manager/window_manager.dart';

/// Keeps Sado in the background on a computer: a tray icon, a hotkey that
/// starts a hands-free talk from any app, and a window that shows up while
/// Sado is busy and slips away when it is idle.
class DesktopShell extends ConsumerStatefulWidget {
  const DesktopShell({required this.child, super.key});

  final Widget child;

  @override
  ConsumerState<DesktopShell> createState() => _DesktopShellState();
}

class _DesktopShellState extends ConsumerState<DesktopShell>
    with TrayListener, WindowListener {
  static const _idleBeforeHiding = Duration(seconds: 20);
  static const _talkKey = 'talk';
  static const _showKey = 'show';
  static const _quitKey = 'quit';

  final _hotkey = HotKey(
    key: PhysicalKeyboardKey.space,
    modifiers: [HotKeyModifier.control, HotKeyModifier.alt],
  );
  Timer? _idle;

  @override
  void initState() {
    super.initState();
    trayManager.addListener(this);
    windowManager.addListener(this);
    unawaited(_setUp());
  }

  Future<void> _setUp() async {
    await trayManager.setIcon('assets/tray_icon.ico');
    await trayManager.setToolTip('Sado — Ctrl+Alt+Space to talk');
    await trayManager.setContextMenu(
      Menu(
        items: [
          MenuItem(key: _talkKey, label: 'Talk to Sado    Ctrl+Alt+Space'),
          MenuItem(key: _showKey, label: 'Show Sado'),
          MenuItem.separator(),
          MenuItem(key: _quitKey, label: 'Quit'),
        ],
      ),
    );
    await hotKeyManager.register(_hotkey, keyDownHandler: (_) => _talk());
  }

  @override
  void dispose() {
    _idle?.cancel();
    trayManager.removeListener(this);
    windowManager.removeListener(this);
    unawaited(hotKeyManager.unregister(_hotkey));
    super.dispose();
  }

  /// The hotkey both starts and stops a conversation, from any app.
  Future<void> _talk() async {
    await DesktopHost.reveal();
    await ref.read(liveConversationProvider.notifier).toggle();
  }

  @override
  void onTrayIconMouseDown() => unawaited(DesktopHost.reveal());

  @override
  void onTrayIconRightMouseDown() => unawaited(trayManager.popUpContextMenu());

  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case _talkKey:
        unawaited(_talk());
      case _showKey:
        unawaited(DesktopHost.reveal());
      case _quitKey:
        unawaited(DesktopHost.quit());
    }
  }

  @override
  void onWindowClose() => unawaited(DesktopHost.hide());

  /// Shows Sado while it has something to say or ask, and hides it after a
  /// quiet spell.
  void _follow(_Activity activity) {
    _idle?.cancel();
    if (activity.busy || activity.needsAnswer) {
      unawaited(DesktopHost.reveal());
      return;
    }
    _idle = Timer(_idleBeforeHiding, () => unawaited(_hideUnlessInUse()));
  }

  /// Never hides under the user's hands: a focused window is being read or
  /// typed into, so the countdown starts over.
  Future<void> _hideUnlessInUse() async {
    if (await windowManager.isFocused()) {
      _idle = Timer(_idleBeforeHiding, () => unawaited(_hideUnlessInUse()));
      return;
    }
    await DesktopHost.hide();
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(_activityProvider, (previous, next) {
      if (previous != next) _follow(next);
    });
    return widget.child;
  }
}

typedef _Activity = ({bool busy, bool needsAnswer});

final _activityProvider = Provider<_Activity>((ref) {
  final live = ref.watch(liveConversationProvider).isLive;
  final speaking = ref.watch(speakControllerProvider).isLoading;
  final thinking = ref.watch(
    conversationControllerProvider.select((state) => state.isThinking),
  );
  final needsAnswer = ref.watch(
    conversationControllerProvider.select(
      (state) => state.lastReply?.pendingAction != null,
    ),
  );
  return (busy: live || speaking || thinking, needsAnswer: needsAnswer);
});
