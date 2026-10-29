import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sado/core/audio/audio_output.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/domain/repositories/speech_repository.dart';
import 'package:sado/features/speech/domain/usecases/speak_text.dart';

class _MockSpeechRepository extends Mock implements SpeechRepository {}

class _MockAudioOutput extends Mock implements AudioOutput {}

void main() {
  late _MockSpeechRepository repository;
  late _MockAudioOutput audioOutput;
  late SpeakText speakText;

  final wav = Uint8List.fromList([1, 2, 3]);

  setUpAll(() {
    registerFallbackValue(Uint8List(0));
    registerFallbackValue(SpokenLanguage.english);
    registerFallbackValue(Mood.neutral);
  });

  setUp(() {
    repository = _MockSpeechRepository();
    audioOutput = _MockAudioOutput();
    speakText = SpeakText(repository, audioOutput);
    when(() => audioOutput.playWav(any())).thenAnswer((_) async {});
  });

  test('plays the synthesized audio', () async {
    when(
      () => repository.synthesize(
        text: 'салом',
        language: SpokenLanguage.tajik,
      ),
    ).thenAnswer((_) async => Ok(wav));

    final result = await speakText(
      text: 'салом',
      language: SpokenLanguage.tajik,
    );

    expect(result, isA<Ok<void>>());
    verify(() => audioOutput.playWav(wav)).called(1);
  });

  test('returns the failure and plays nothing when synthesis fails', () async {
    when(
      () => repository.synthesize(
        text: any(named: 'text'),
        language: any(named: 'language'),
      ),
    ).thenAnswer((_) async => const Err(NetworkFailure('offline')));

    final result = await speakText(
      text: 'hello',
      language: SpokenLanguage.english,
    );

    expect(
      result,
      isA<Err<void>>().having(
        (err) => err.failure.message,
        'message',
        'offline',
      ),
    );
    verifyNever(() => audioOutput.playWav(any()));
  });

  test('asks for the chosen voice and mood', () async {
    when(
      () => repository.synthesize(
        text: any(named: 'text'),
        language: any(named: 'language'),
        voiceId: any(named: 'voiceId'),
        mood: any(named: 'mood'),
      ),
    ).thenAnswer((_) async => Ok(wav));

    await speakText(
      text: 'salom',
      language: SpokenLanguage.uzbek,
      voiceId: 'opa',
      mood: Mood.happy,
    );

    verify(
      () => repository.synthesize(
        text: 'salom',
        language: SpokenLanguage.uzbek,
        voiceId: 'opa',
        mood: Mood.happy,
      ),
    ).called(1);
  });

  test('voices the next sentence while the current one plays', () async {
    final events = <String>[];
    when(
      () => repository.synthesize(
        text: any(named: 'text'),
        language: any(named: 'language'),
      ),
    ).thenAnswer((invocation) async {
      final text = invocation.namedArguments[#text] as String;
      events.add('voice $text');
      return Ok(Uint8List.fromList(text.codeUnits));
    });
    when(() => audioOutput.playWav(any())).thenAnswer((invocation) async {
      final bytes = invocation.positionalArguments.first as Uint8List;
      events.add('play ${String.fromCharCodes(bytes)}');
    });

    await speakText(
      text: 'Birinchi gap shu yerda. Ikkinchi gap esa mana bu.',
      language: SpokenLanguage.uzbek,
    );

    expect(events, [
      'voice Birinchi gap shu yerda.',
      'voice Ikkinchi gap esa mana bu.',
      'play Birinchi gap shu yerda.',
      'play Ikkinchi gap esa mana bu.',
    ]);
  });

  test('stops between sentences once the caller gives up', () async {
    when(
      () => repository.synthesize(
        text: any(named: 'text'),
        language: any(named: 'language'),
      ),
    ).thenAnswer((_) async => Ok(wav));
    var wanted = true;
    when(() => audioOutput.playWav(any())).thenAnswer((_) async {
      wanted = false;
    });

    await speakText(
      text: 'Birinchi gap shu yerda. Ikkinchi gap esa mana bu.',
      language: SpokenLanguage.uzbek,
      stillWanted: () => wanted,
    );

    verify(() => audioOutput.playWav(any())).called(1);
  });
}
