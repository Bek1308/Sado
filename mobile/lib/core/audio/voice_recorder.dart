final class RecordedAudio {
  const RecordedAudio({required this.path, required this.mimeType});

  final String path;
  final String mimeType;
}

abstract interface class VoiceRecorder {
  /// Starts capturing the microphone. Returns `false` when the user denies
  /// microphone access.
  Future<bool> start();

  /// Stops capturing and returns the recording, or `null` if nothing was
  /// being recorded.
  Future<RecordedAudio?> stop();
}
