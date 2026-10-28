import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final spokenLanguageProvider =
    NotifierProvider<SpokenLanguageSetting, SpokenLanguage>(
      SpokenLanguageSetting.new,
    );

/// The language Sado currently hears and answers in. Nobody picks it by
/// hand: every transcription updates it to the detected language.
class SpokenLanguageSetting extends Notifier<SpokenLanguage> {
  @override
  SpokenLanguage build() => SpokenLanguage.uzbek;

  SpokenLanguage get current => state;

  /// Remembers the language the server detected in the last recording.
  set current(SpokenLanguage language) => state = language;
}

final moodProvider = NotifierProvider<MoodSetting, Mood>(MoodSetting.new);

class MoodSetting extends Notifier<Mood> {
  @override
  Mood build() => Mood.neutral;

  Mood get selected => state;
  set selected(Mood mood) => state = mood;
}
