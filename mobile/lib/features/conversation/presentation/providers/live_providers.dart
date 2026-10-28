import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/audioplayers_output.dart';
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

  bool _running = false;
  // Released through _cancelWatchers when a turn ends or the user stops.
  // ignore: cancel_subscriptions
  StreamSubscription<double>? _levels;
  Timer? _silenceTimer;
  Timer? _maxTimer;

  @override
  LiveState build() {
    ref.onDispose(_cancelWatchers);
    return const LiveState();
  }

  Future<void> toggle() => state.isLive ? stop() : start();

  Future<void> start() async {
    if (_running) return;
    _running = true;
    await _beginTurn();
  }

  Future<void> stop() async {
    _running = false;
    _cancelWatchers();
    await ref.read(voiceRecorderProvider).stop();
    await ref.read(audioOutputProvider).stop();
    state = const LiveState();
  }

  Future<void> _beginTurn() async {
    if (!_running) return;
    state = const LiveState(phase: LivePhase.listening);
    await ref.read(listeningControllerProvider.notifier).start();
    if (!_running) return;
    if (ref.read(listeningControllerProvider) is ListeningFailed) {
      return _fail('Microphone access was denied');
    }
    var heardSpeech = false;
    _levels = ref.read(voiceRecorderProvider).levels.listen((level) {
      if (!_running) return;
      if (level >= _speechThresholdDb) {
        heardSpeech = true;
        _silenceTimer?.cancel();
        _silenceTimer = null;
      } else if (heardSpeech && _silenceTimer == null) {
        _silenceTimer = Timer(_silenceTimeout, _finishTurn);
      }
    });
    _maxTimer = Timer(_maxTurn, _finishTurn);
  }

  Future<void> _finishTurn() async {
    _cancelWatchers();
    if (!_running) return;
    state = const LiveState(phase: LivePhase.thinking);
    await ref.read(listeningControllerProvider.notifier).stop();
    if (!_running) return;
    switch (ref.read(listeningControllerProvider)) {
      case ListeningHeard(:final text) when text.trim().isEmpty:
        return _beginTurn();
      case ListeningHeard(:final text):
        final reply = await ref
            .read(conversationControllerProvider.notifier)
            .ask(
              text,
              ref.read(spokenLanguageProvider),
              ref.read(sadoModeProvider),
            );
        if (!_running) return;
        if (reply == null) return _fail('Sado could not answer');
        state = const LiveState(phase: LivePhase.speaking);
        await ref.read(speakControllerProvider.notifier).say(reply.text);
        if (!_running) return;
        return _beginTurn();
      case ListeningFailed(:final message):
        return _fail(message);
      case ListeningIdle():
        return _beginTurn();
      default:
        return _fail('Sado heard nothing');
    }
  }

  void _fail(String message) {
    _running = false;
    _cancelWatchers();
    state = LiveState(error: message);
  }

  void _cancelWatchers() {
    final levels = _levels;
    _levels = null;
    unawaited(levels?.cancel());
    _silenceTimer?.cancel();
    _silenceTimer = null;
    _maxTimer?.cancel();
    _maxTimer = null;
  }
}
