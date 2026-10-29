import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/record_voice_recorder.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_settings_providers.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

enum LivePhase { idle, listening, thinking, speaking }

final class LiveState {
  const LiveState({this.phase = LivePhase.idle, this.error});

  final LivePhase phase;
  final String? error;

  bool get isLive => phase != LivePhase.idle;
}

final liveConversationProvider =
    NotifierProvider<LiveConversationController, LiveState>(
      LiveConversationController.new,
    );

/// A hands-free conversation: Sado listens until the user goes quiet, thinks,
/// speaks the answer, and listens again — until the user stops it.
class LiveConversationController extends Notifier<LiveState> {
  /// Loudness at or above this counts as speech; below it is silence.
  static const _speechThresholdDb = -35.0;

  /// A turn ends after this much silence once speech was heard.
  static const _silenceTimeout = Duration(milliseconds: 1200);

  /// The speech worker caps utterances at 40 seconds.
  static const _maxTurn = Duration(seconds: 38);

  /// Every start and stop opens a new session. Each step of a turn checks it
  /// still belongs to the current one after every wait, so a turn that
  /// outlives a Stop or a quick restart quietly ends instead of racing.
  int _session = 0;

  // Released through _cancelWatchers when a turn ends or the user stops.
  // ignore: cancel_subscriptions
  StreamSubscription<double>? _levels;
  Timer? _silenceTimer;
  Timer? _maxTimer;

  @override
  LiveState build() {
    // Providers cannot be touched while this one is being disposed.
    ref.onDispose(() => _cancelWatchers(quietMic: false));
    return const LiveState();
  }

  Future<void> toggle() => state.isLive ? stop() : start();

  Future<void> start() async {
    if (state.isLive) return;
    final session = ++_session;
    await _beginTurn(session);
  }

  Future<void> stop() async {
    _session++;
    _cancelWatchers();
    state = const LiveState();
    await ref.read(listeningControllerProvider.notifier).cancel();
    await ref.read(speakControllerProvider.notifier).stop();
  }

  bool _isStale(int session) => session != _session;

  Future<void> _beginTurn(int session) async {
    if (_isStale(session)) return;
    state = const LiveState(phase: LivePhase.listening);
    final listening = ref.read(listeningControllerProvider.notifier);
    await listening.start();
    if (_isStale(session)) {
      // Stop arrived while the microphone was opening; close it again.
      await listening.cancel();
      return;
    }
    if (ref.read(listeningControllerProvider) is ListeningFailed) {
      return _fail(session, 'Microphone access was denied');
    }
    var heardSpeech = false;
    _levels = ref.read(voiceRecorderProvider).levels.listen((level) {
      if (_isStale(session)) return;
      ref.read(micLevelProvider.notifier).hear(level);
      if (level >= _speechThresholdDb) {
        heardSpeech = true;
        _silenceTimer?.cancel();
        _silenceTimer = null;
      } else if (heardSpeech && _silenceTimer == null) {
        _silenceTimer = Timer(_silenceTimeout, () => _finishTurn(session));
      }
    });
    _maxTimer = Timer(
      _maxTurn,
      () => heardSpeech ? _finishTurn(session) : _listenAgain(session),
    );
  }

  /// Nobody spoke for a whole turn: drop the silence instead of uploading it.
  Future<void> _listenAgain(int session) async {
    if (_isStale(session)) return;
    _cancelWatchers();
    await ref.read(listeningControllerProvider.notifier).cancel();
    await _beginTurn(session);
  }

  Future<void> _finishTurn(int session) async {
    if (_isStale(session)) return;
    _cancelWatchers();
    state = const LiveState(phase: LivePhase.thinking);
    await ref.read(listeningControllerProvider.notifier).stop();
    if (_isStale(session)) return;
    switch (ref.read(listeningControllerProvider)) {
      case ListeningHeard(:final text) when text.trim().isEmpty:
        return _beginTurn(session);
      case ListeningHeard(:final text):
        final reply = await ref
            .read(conversationControllerProvider.notifier)
            .ask(
              text,
              ref.read(spokenLanguageProvider),
              ref.read(sadoModeProvider),
            );
        if (_isStale(session)) return;
        if (reply == null) {
          final why = ref.read(conversationControllerProvider).error;
          return _fail(session, why ?? 'Sado could not answer');
        }
        state = const LiveState(phase: LivePhase.speaking);
        await ref.read(speakControllerProvider.notifier).say(reply.text);
        if (_isStale(session)) return;
        return _beginTurn(session);
      case ListeningFailed(:final message):
        return _fail(session, message);
      case ListeningIdle():
        return _beginTurn(session);
      default:
        return _fail(session, 'Sado heard nothing');
    }
  }

  void _fail(int session, String message) {
    if (_isStale(session)) return;
    _session++;
    _cancelWatchers();
    state = LiveState(error: message);
  }

  void _cancelWatchers({bool quietMic = true}) {
    if (quietMic) ref.read(micLevelProvider.notifier).quiet();
    final levels = _levels;
    _levels = null;
    unawaited(levels?.cancel());
    _silenceTimer?.cancel();
    _silenceTimer = null;
    _maxTimer?.cancel();
    _maxTimer = null;
  }
}
