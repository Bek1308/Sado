import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:sado/core/audio/voice_recorder.dart';

final voiceRecorderProvider = Provider<VoiceRecorder>((ref) {
  final recorder = AudioRecorder();
  ref.onDispose(recorder.dispose);
  return RecordVoiceRecorder(recorder);
});

final class RecordVoiceRecorder implements VoiceRecorder {
  const RecordVoiceRecorder(this._recorder);

  // Speech models work at 16 kHz mono; recording at that rate keeps uploads
  // small. The default encoder is AAC, saved as .m4a.
  static const _config = RecordConfig(
    sampleRate: 16000,
    numChannels: 1,
  );
  static const _mimeType = 'audio/mp4';
  static const _levelInterval = Duration(milliseconds: 200);

  final AudioRecorder _recorder;

  @override
  Stream<double> get levels => _recorder
      .onAmplitudeChanged(_levelInterval)
      .map((amplitude) => amplitude.current);

  @override
  Future<bool> start() async {
    if (!await _recorder.hasPermission()) return false;
    final folder = await getTemporaryDirectory();
    final fileName = 'sado_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(_config, path: '${folder.path}/$fileName');
    return true;
  }

  @override
  Future<RecordedAudio?> stop() async {
    final path = await _recorder.stop();
    return path == null ? null : RecordedAudio(path: path, mimeType: _mimeType);
  }
}
