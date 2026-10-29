import 'dart:typed_data';

abstract interface class AudioOutput {
  /// Plays the audio and completes when playback finishes or [stop] is called.
  Future<void> playWav(Uint8List wavBytes);

  /// Stops playback; a pending [playWav] completes right away.
  Future<void> stop();

  /// How loud the playing audio is right now, from 0 to 1, many times a
  /// second; 0 when nothing plays.
  Stream<double> get loudness;
}
