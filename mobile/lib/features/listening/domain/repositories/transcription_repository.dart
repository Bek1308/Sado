import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/listening/domain/entities/transcription.dart';

abstract interface class TranscriptionRepository {
  /// Returns what was said in the recording, with the detected language.
  Future<Result<Transcription>> transcribe(RecordedAudio recording);
}
