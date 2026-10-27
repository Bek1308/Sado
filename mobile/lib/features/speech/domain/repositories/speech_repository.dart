import 'dart:typed_data';

import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

abstract interface class SpeechRepository {
  /// Returns the text spoken aloud as WAV audio.
  ///
  /// A `null` [voiceId] means the server's default voice.
  Future<Result<Uint8List>> synthesize({
    required String text,
    required SpokenLanguage language,
    String? voiceId,
    Mood mood = Mood.neutral,
  });
}
