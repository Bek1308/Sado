import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/listening/domain/repositories/transcription_repository.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final class TranscribeRecording {
  const TranscribeRecording(this._repository);

  final TranscriptionRepository _repository;

  Future<Result<String>> call(
    RecordedAudio recording,
    SpokenLanguage language,
  ) => _repository.transcribe(recording, language);
}
