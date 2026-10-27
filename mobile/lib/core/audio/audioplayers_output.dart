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
  const AudioplayersOutput(this._player);

  final AudioPlayer _player;

  @override
  Future<void> playWav(Uint8List wavBytes) async {
    await _player.stop();
    await _player.play(BytesSource(wavBytes, mimeType: 'audio/wav'));
  }
}
