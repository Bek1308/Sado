import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/audioplayers_output.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/speech/data/datasources/speech_remote_data_source.dart';
import 'package:sado/features/speech/data/repositories/speech_repository_impl.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/domain/repositories/speech_repository.dart';
import 'package:sado/features/speech/domain/usecases/speak_text.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';
import 'package:sado/features/voices/presentation/providers/voice_providers.dart';

final speechRepositoryProvider = Provider<SpeechRepository>(
  (ref) => SpeechRepositoryImpl(
    SpeechRemoteDataSource(ref.watch(httpClientProvider)),
  ),
);

final speakTextProvider = Provider<SpeakText>(
  (ref) => SpeakText(
    ref.watch(speechRepositoryProvider),
    ref.watch(audioOutputProvider),
  ),
);

final speakControllerProvider = AsyncNotifierProvider<SpeakController, void>(
  SpeakController.new,
);

class SpeakController extends AsyncNotifier<void> {
  // Synchronous, so Sado starts out idle instead of looking busy for a frame.
  @override
  FutureOr<void> build() {}

  Future<void> speak(
    String text,
    SpokenLanguage language, {
    String? voiceId,
    Mood mood = Mood.neutral,
  }) async {
    state = const AsyncLoading();
    final result = await ref
        .read(speakTextProvider)
        .call(
          text: text,
          language: language,
          voiceId: voiceId,
          mood: mood,
        );
    state = switch (result) {
      Ok() => const AsyncData(null),
      Err(:final failure) => AsyncError(failure, StackTrace.current),
    };
  }

  /// Speaks [text] in the language, voice and mood the user has chosen.
  Future<void> say(String text) => speak(
    text,
    ref.read(spokenLanguageProvider),
    voiceId: ref.read(selectedVoiceIdProvider),
    mood: ref.read(moodProvider),
  );
}
