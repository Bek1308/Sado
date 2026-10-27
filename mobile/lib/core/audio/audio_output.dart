import 'dart:typed_data';

abstract interface class AudioOutput {
  Future<void> playWav(Uint8List wavBytes);
}
