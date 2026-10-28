import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

abstract interface class TranscriptionRepository {
  /// Returns what was said in the recording, as text.
  Future<Result<String>> transcribe(
    RecordedAudio recording,
    SpokenLanguage language,
  );
}
