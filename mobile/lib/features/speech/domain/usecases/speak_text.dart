import 'package:sado/core/audio/audio_output.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/domain/repositories/speech_repository.dart';

final class SpeakText {
  const SpeakText(this._repository, this._audioOutput);

  final SpeechRepository _repository;
  final AudioOutput _audioOutput;

  Future<Result<void>> call({
    required String text,
    required SpokenLanguage language,
    String? voiceId,
  }) async {
    final result = await _repository.synthesize(
      text: text,
      language: language,
      voiceId: voiceId,
    );
    switch (result) {
      case Ok(:final value):
        await _audioOutput.playWav(value);
        return const Ok(null);
      case Err(:final failure):
        return Err(failure);
    }
  }
}
