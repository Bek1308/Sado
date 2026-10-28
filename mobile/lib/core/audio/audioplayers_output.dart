import 'dart:async';
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/audio_output.dart';

final audioOutputProvider = Provider<AudioOutput>((ref) {
  final player = AudioPlayer();
  ref.onDispose(player.dispose);
  return AudioplayersOutput(player);
});

final class AudioplayersOutput implements AudioOutput {
  AudioplayersOutput(this._player);

  final AudioPlayer _player;
  Completer<void>? _stopSignal;

  @override
  Future<void> playWav(Uint8List wavBytes) async {
    // The player stays silent about stops, so a pending playback is released
    // through its own signal instead of the completion event.
    _stopSignal?.complete();
    await _player.stop();
    final signal = Completer<void>();
    _stopSignal = signal;
    try {
      await _player.play(BytesSource(wavBytes, mimeType: 'audio/wav'));
      await Future.any([_player.onPlayerComplete.first, signal.future]);
    } finally {
      if (identical(_stopSignal, signal)) _stopSignal = null;
    }
  }

  @override
  Future<void> stop() async {
    _stopSignal?.complete();
    await _player.stop();
  }
}
