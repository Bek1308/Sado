import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/listening/domain/entities/transcription.dart';
import 'package:sado/features/listening/domain/repositories/transcription_repository.dart';

final class TranscribeRecording {
  const TranscribeRecording(this._repository);

  final TranscriptionRepository _repository;

  Future<Result<Transcription>> call(RecordedAudio recording) =>
      _repository.transcribe(recording);
}
