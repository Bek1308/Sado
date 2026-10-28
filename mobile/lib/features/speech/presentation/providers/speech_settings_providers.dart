import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final spokenLanguageProvider =
    NotifierProvider<SpokenLanguageSetting, SpokenLanguage>(
      SpokenLanguageSetting.new,
    );

class SpokenLanguageSetting extends Notifier<SpokenLanguage> {
  @override
  SpokenLanguage build() => SpokenLanguage.tajik;

  SpokenLanguage get selected => state;
  set selected(SpokenLanguage language) => state = language;
}

final moodProvider = NotifierProvider<MoodSetting, Mood>(MoodSetting.new);

class MoodSetting extends Notifier<Mood> {
  @override
  Mood build() => Mood.neutral;

  Mood get selected => state;
  set selected(Mood mood) => state = mood;
}
