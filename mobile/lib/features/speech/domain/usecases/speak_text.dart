import 'package:sado/core/audio/audio_output.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/domain/repositories/speech_repository.dart';

final class SpeakText {
  const SpeakText(this._repository, this._audioOutput);

  final SpeechRepository _repository;
  final AudioOutput _audioOutput;

  /// Synthesizes [text] and plays it, unless [stillWanted] says the caller
  /// gave up while the voice was being prepared.
  Future<Result<void>> call({
    required String text,
    required SpokenLanguage language,
    String? voiceId,
    Mood mood = Mood.neutral,
    bool Function()? stillWanted,
  }) async {
    final result = await _repository.synthesize(
      text: text,
      language: language,
      voiceId: voiceId,
      mood: mood,
    );
    switch (result) {
      case Ok(:final value):
        if (stillWanted?.call() ?? true) await _audioOutput.playWav(value);
        return const Ok(null);
      case Err(:final failure):
        return Err(failure);
    }
  }
}
