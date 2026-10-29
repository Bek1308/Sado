import 'dart:async';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/audio_output.dart';
import 'package:sado/core/audio/wav_envelope.dart';

final audioOutputProvider = Provider<AudioOutput>((ref) {
  final player = AudioPlayer();
  final output = AudioplayersOutput(player);
  ref.onDispose(() async {
    await output.dispose();
    await player.dispose();
  });
  return output;
});

final class AudioplayersOutput implements AudioOutput {
  AudioplayersOutput(this._player);

  static const _frame = Duration(milliseconds: 50);
  static const _tick = Duration(milliseconds: 33);

  final AudioPlayer _player;
  final _loudness = StreamController<double>.broadcast();
  Completer<void>? _stopSignal;
  Timer? _meter;

  @override
  Stream<double> get loudness => _loudness.stream;

  @override
  Future<void> playWav(Uint8List wavBytes) async {
    // The player stays silent about stops, so a pending playback is released
    // through its own signal instead of the completion event.
    _stopSignal?.complete();
    await _player.stop();
    final signal = Completer<void>();
    _stopSignal = signal;
    final envelope = wavEnvelope(wavBytes, frame: _frame);
    // Listen before playing: a very short clip can finish before play()
    // returns.
    final finished = _player.onPlayerComplete.first;
    try {
      await _player.play(BytesSource(wavBytes, mimeType: 'audio/wav'));
      _startMeter(envelope);
      await Future.any([finished, signal.future]);
    } finally {
      _stopMeter();
      if (identical(_stopSignal, signal)) _stopSignal = null;
    }
  }

  @override
  Future<void> stop() async {
    _stopSignal?.complete();
    _stopMeter();
    await _player.stop();
  }

  Future<void> dispose() async {
    _stopMeter();
    await _loudness.close();
  }

  /// The player reports no levels, so a clock walks through the clip's own
  /// envelope in step with playback.
  void _startMeter(List<double> envelope) {
    _stopMeter();
    if (envelope.isEmpty) return;
    final clock = Stopwatch()..start();
    _meter = Timer.periodic(_tick, (_) {
      final index = clock.elapsedMicroseconds ~/ _frame.inMicroseconds;
      _loudness.add(index < envelope.length ? envelope[index] : 0);
    });
  }

  void _stopMeter() {
    _meter?.cancel();
    _meter = null;
    if (!_loudness.isClosed) _loudness.add(0);
  }
}
