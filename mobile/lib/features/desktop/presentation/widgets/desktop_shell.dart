import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hotkey_manager/hotkey_manager.dart';
import 'package:sado/core/desktop/desktop_host.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/desktop/presentation/providers/desktop_view_providers.dart';
import 'package:sado/features/desktop/presentation/widgets/compact_voice_bar.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:tray_manager/tray_manager.dart';
import 'package:window_manager/window_manager.dart';

/// Keeps Sado out of sight on a computer. It lives in the tray; the hotkey
/// brings up only a slim voice bar and starts talking right away, and the
/// bar goes again once the conversation is over. Saying "Sado" does the same
/// as the hotkey. The full window opens from the tray.
class DesktopShell extends ConsumerStatefulWidget {
  const DesktopShell({required this.child, super.key});

  final Widget child;

  @override
  ConsumerState<DesktopShell> createState() => _DesktopShellState();
}

class _DesktopShellState extends ConsumerState<DesktopShell>
    with TrayListener, WindowListener {
  /// A short beat after Sado finishes, so its last words are not cut off.
  static const _lingerAfterTalk = Duration(milliseconds: 2500);
  static const _talkKey = 'talk';
  static const _openKey = 'open';
  static const _quitKey = 'quit';

  final _hotkey = HotKey(
    key: PhysicalKeyboardKey.keyS,
    modifiers: [HotKeyModifier.control, HotKeyModifier.alt],
  );
  Timer? _hideTimer;
  bool _listeningForName = true;

  @override
  void initState() {
    super.initState();
    trayManager.addListener(this);
    windowManager.addListener(this);
    unawaited(_setUp());
    unawaited(_answerWhenCalled());
  }

  /// Says "Sado" and Sado comes: the server hears the name on the microphone,
  /// and this waits for it.
  Future<void> _answerWhenCalled() async {
    final http = ref.read(httpClientProvider);
    var seen = -1;
    while (_listeningForName && mounted) {
      try {
        final response = await http.get<Map<String, dynamic>>(
          '/desktop/wake',
          queryParameters: {'after': seen},
        );
        final count = response.data?['count'] as int? ?? seen;
        // The first answer only says where the count stands.
        final called = seen >= 0 && count > seen;
        seen = count;
        // Sado saying its own name mid-answer must not restart the talk.
        if (called && !ref.read(_activityProvider).busy) await _talk();
      } on DioException {
        // The server is away; ask again in a moment.
        await Future<void>.delayed(const Duration(seconds: 5));
      }
    }
  }

  Future<void> _setUp() async {
    await trayManager.setIcon('assets/tray_icon.ico');
    await trayManager.setToolTip('Sado — Ctrl+Alt+S to talk');
    await trayManager.setContextMenu(
      Menu(
        items: [
          MenuItem(key: _talkKey, label: 'Talk to Sado    Ctrl+Alt+S'),
          MenuItem(key: _openKey, label: 'Open Sado'),
          MenuItem.separator(),
          MenuItem(key: _quitKey, label: 'Quit'),
        ],
      ),
    );
    await hotKeyManager.register(_hotkey, keyDownHandler: (_) => _talk());
  }

  @override
  void dispose() {
    _listeningForName = false;
    _hideTimer?.cancel();
    trayManager.removeListener(this);
    windowManager.removeListener(this);
    unawaited(hotKeyManager.unregister(_hotkey));
    super.dispose();
  }

  DesktopView get _view => ref.read(desktopViewProvider);

  set _view(DesktopView view) =>
      ref.read(desktopViewProvider.notifier).current = view;

  /// The hotkey starts a conversation from any app, or ends the current one.
  Future<void> _talk() async {
    final live = ref.read(liveConversationProvider.notifier);
    if (ref.read(liveConversationProvider).isLive) {
      await live.stop();
      return;
    }
    if (_view != DesktopView.full) _view = DesktopView.compact;
    await live.start();
  }

  @override
  void onTrayIconMouseDown() => _view = DesktopView.full;

  @override
  void onTrayIconRightMouseDown() => unawaited(trayManager.popUpContextMenu());

  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case _talkKey:
        unawaited(_talk());
      case _openKey:
        _view = DesktopView.full;
      case _quitKey:
        unawaited(DesktopHost.quit());
    }
  }

  @override
  void onWindowClose() => _view = DesktopView.hidden;

  Future<void> _show(DesktopView view, {required bool asking}) =>
      switch (view) {
        DesktopView.hidden => DesktopHost.hide(),
        DesktopView.compact => DesktopHost.showCompact(asking: asking),
        DesktopView.full => DesktopHost.showFull(),
      };

  /// The voice bar leaves once Sado is done and has nothing left to ask.
  void _follow(_Activity activity) {
    _hideTimer?.cancel();
    if (_view != DesktopView.compact) return;
    unawaited(DesktopHost.showCompact(asking: activity.asking));
    if (activity.busy || activity.asking) return;
    _hideTimer = Timer(_lingerAfterTalk, () {
      if (_view == DesktopView.compact) _view = DesktopView.hidden;
    });
  }

  @override
  Widget build(BuildContext context) {
    ref
      ..listen(desktopViewProvider, (_, view) {
        _hideTimer?.cancel();
        unawaited(_show(view, asking: ref.read(_activityProvider).asking));
      })
      ..listen(_activityProvider, (previous, next) {
        if (previous != next) _follow(next);
      });
    final compact = ref.watch(desktopViewProvider) == DesktopView.compact;
    // The full app stays alive behind the bar, so the conversation and its
    // state carry over when the window opens.
    return Stack(
      children: [
        Offstage(offstage: compact, child: widget.child),
        if (compact) const CompactVoiceBar(),
      ],
    );
  }
}

typedef _Activity = ({bool busy, bool asking});

final _activityProvider = Provider<_Activity>((ref) {
  final live = ref.watch(liveConversationProvider).isLive;
  final speaking = ref.watch(speakControllerProvider).isLoading;
  final thinking = ref.watch(
    conversationControllerProvider.select((state) => state.isThinking),
  );
  final asking = ref.watch(
    conversationControllerProvider.select(
      (state) => state.lastReply?.pendingAction != null,
    ),
  );
  return (busy: live || speaking || thinking, asking: asking);
});
