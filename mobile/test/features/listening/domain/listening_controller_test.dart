import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/audio/record_voice_recorder.dart';
import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/listening/domain/entities/transcription.dart';
import 'package:sado/features/listening/domain/repositories/transcription_repository.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

const _recording = RecordedAudio(path: '/tmp/a.m4a', mimeType: 'audio/mp4');

final class _FakeRecorder implements VoiceRecorder {
  _FakeRecorder({this.allowed = true});

  final bool allowed;

  @override
  Future<bool> start() async => allowed;

  @override
  Future<RecordedAudio?> stop() async => _recording;

  @override
  Stream<double> get levels => const Stream.empty();
}

final class _FakeRepository implements TranscriptionRepository {
  _FakeRepository(this.result);

  final Result<Transcription> result;

  @override
  Future<Result<Transcription>> transcribe(RecordedAudio recording) async =>
      result;
}

ProviderContainer _container(
  _FakeRepository repository, {
  bool microphoneAllowed = true,
}) {
  final container = ProviderContainer(
    overrides: [
      voiceRecorderProvider.overrideWithValue(
        _FakeRecorder(allowed: microphoneAllowed),
      ),
      transcriptionRepositoryProvider.overrideWithValue(repository),
    ],
  );
  addTearDown(container.dispose);
  return container;
}

void main() {
  test('records, then shows what was heard in the detected language', () async {
    final repository = _FakeRepository(
      const Ok((text: 'салом', language: SpokenLanguage.tajik)),
    );
    final container = _container(repository);
    final controller = container.read(listeningControllerProvider.notifier);

    await controller.start();
    expect(
      container.read(listeningControllerProvider),
      isA<ListeningRecording>(),
    );

    await controller.stop();

    expect(
      container.read(listeningControllerProvider),
      isA<ListeningHeard>()
          .having((heard) => heard.text, 'text', 'салом')
          .having(
            (heard) => heard.language,
            'language',
            SpokenLanguage.tajik,
          ),
    );
    expect(
      container.read(spokenLanguageProvider),
      SpokenLanguage.tajik,
    );
  });

  test('reports a denied microphone', () async {
    final container = _container(
      _FakeRepository(
        const Ok((text: '', language: SpokenLanguage.uzbek)),
      ),
      microphoneAllowed: false,
    );

    await container.read(listeningControllerProvider.notifier).start();

    expect(container.read(listeningControllerProvider), isA<ListeningFailed>());
  });

  test('reports a failed transcription', () async {
    final container = _container(
      _FakeRepository(const Err(NetworkFailure('Server is unreachable'))),
    );
    final controller = container.read(listeningControllerProvider.notifier);

    await controller.start();
    await controller.stop();

    expect(
      container.read(listeningControllerProvider),
      isA<ListeningFailed>().having(
        (failed) => failed.message,
        'message',
        'Server is unreachable',
      ),
    );
  });
}
