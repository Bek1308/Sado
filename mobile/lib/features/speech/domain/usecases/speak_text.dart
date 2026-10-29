import 'dart:typed_data';

import 'package:sado/core/audio/audio_output.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_chunks.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/domain/repositories/speech_repository.dart';

final class SpeakText {
  const SpeakText(this._repository, this._audioOutput);

  final SpeechRepository _repository;
  final AudioOutput _audioOutput;

  /// Speaks [text] sentence by sentence: each sentence plays while the next
  /// one is being voiced, so Sado starts talking after the first sentence
  /// instead of after the whole reply. Stops early once [stillWanted] says
  /// the caller gave up.
  Future<Result<void>> call({
    required String text,
    required SpokenLanguage language,
    String? voiceId,
    Mood mood = Mood.neutral,
    bool Function()? stillWanted,
  }) async {
    Future<Result<Uint8List>> voice(String chunk) => _repository.synthesize(
      text: chunk,
      language: language,
      voiceId: voiceId,
      mood: mood,
    );

    final chunks = spokenChunks(text);
    if (chunks.isEmpty) return const Ok(null);
    var next = voice(chunks.first);
    for (var index = 0; index < chunks.length; index++) {
      final result = await next;
      if (index + 1 < chunks.length) next = voice(chunks[index + 1]);
      switch (result) {
        case Err(:final failure):
          return Err(failure);
        case Ok(:final value):
          if (!(stillWanted?.call() ?? true)) return const Ok(null);
          await _audioOutput.playWav(value);
      }
    }
    return const Ok(null);
  }
}
