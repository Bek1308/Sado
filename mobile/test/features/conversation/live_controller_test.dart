import 'dart:async';
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/audio/audio_output.dart';
import 'package:sado/core/audio/audioplayers_output.dart';
import 'package:sado/core/audio/record_voice_recorder.dart';
import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/listening/domain/entities/transcription.dart';
import 'package:sado/features/listening/domain/repositories/transcription_repository.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/domain/repositories/speech_repository.dart';
import 'package:sado/features/speech/domain/usecases/speak_text.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';

const _recording = RecordedAudio(path: '/tmp/a.m4a', mimeType: 'audio/mp4');

final class _FakeRecorder implements VoiceRecorder {
  int stopCalls = 0;
  bool recording = false;

  /// When set, opening the microphone waits for it, like a permission prompt.
  Completer<void>? startGate;

  @override
  Future<bool> start() async {
    await startGate?.future;
    recording = true;
    return true;
  }

  @override
  Future<RecordedAudio?> stop() async {
    stopCalls++;
    recording = false;
    return _recording;
  }

  /// Speech, then silence: the turn ends 1.2 s after the last sample.
  @override
  Stream<double> get levels => Stream.fromIterable([-50, -20, -20, -50]);
}

final class _FakeTranscriptions implements TranscriptionRepository {
  const _FakeTranscriptions(this.result);

  final Result<Transcription> result;

  @override
  Future<Result<Transcription>> transcribe(RecordedAudio recording) async =>
      result;
}

final class _FakeConversation implements ConversationRepository {
  int asked = 0;

  /// When set, the first answer waits for it, like a slow model.
  Completer<void>? firstAnswerGate;

  @override
  Future<Result<SadoReply>> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) async {
    asked++;
    if (asked == 1) await firstAnswerGate?.future;
    return const Ok(SadoReply(text: 'Salom!'));
  }
}

final class _FakeSpeech implements SpeechRepository {
  final List<String> said = [];

  @override
  Future<Result<Uint8List>> synthesize({
    required String text,
    required SpokenLanguage language,
    String? voiceId,
    Mood mood = Mood.neutral,
  }) async {
    said.add(text);
    return Ok(Uint8List(0));
  }
}

final class _FakeAudio implements AudioOutput {
  int stopCalls = 0;
  int played = 0;

  @override
  Future<void> playWav(Uint8List wavBytes) async {
    played++;
  }

  @override
  Future<void> stop() async {
    stopCalls++;
  }

  @override
  Stream<double> get loudness => const Stream.empty();
}

ProviderContainer _container({
  required _FakeConversation conversation,
  required _FakeSpeech speech,
  required _FakeAudio audio,
  _FakeRecorder? recorder,
  Result<Transcription> heard = const Ok((
    text: 'salom',
    language: SpokenLanguage.uzbek,
  )),
}) {
  final container = ProviderContainer(
    overrides: [
      voiceRecorderProvider.overrideWithValue(recorder ?? _FakeRecorder()),
      transcriptionRepositoryProvider.overrideWithValue(
        _FakeTranscriptions(heard),
      ),
      conversationRepositoryProvider.overrideWithValue(conversation),
      speakTextProvider.overrideWithValue(SpeakText(speech, audio)),
      audioOutputProvider.overrideWithValue(audio),
    ],
  );
  addTearDown(container.dispose);
  return container;
}

void main() {
  test('listens, answers and speaks, then listens again', () async {
    final conversation = _FakeConversation();
    final speech = _FakeSpeech();
    final audio = _FakeAudio();
    final container = _container(
      conversation: conversation,
      speech: speech,
      audio: audio,
    );
    final controller = container.read(liveConversationProvider.notifier);

    await controller.start();
    expect(
      container.read(liveConversationProvider).phase,
      LivePhase.listening,
    );

    // Speech, then 1.2 s of silence ends the turn.
    await Future<void>.delayed(const Duration(seconds: 2));

    expect(conversation.asked, 1);
    expect(speech.said, ['Salom!']);
    expect(
      container.read(liveConversationProvider).phase,
      LivePhase.listening,
    );

    await controller.stop();
    expect(container.read(liveConversationProvider).isLive, isFalse);
    expect(audio.stopCalls, 1);
  });

  test('keeps listening when nothing was heard', () async {
    final conversation = _FakeConversation();
    final container = _container(
      conversation: conversation,
      speech: _FakeSpeech(),
      audio: _FakeAudio(),
      heard: const Ok((text: '  ', language: SpokenLanguage.uzbek)),
    );

    await container.read(liveConversationProvider.notifier).start();
    await Future<void>.delayed(const Duration(seconds: 2));

    expect(conversation.asked, 0);
    expect(
      container.read(liveConversationProvider).phase,
      LivePhase.listening,
    );
  });

  test('a reply that arrives after Stop is not spoken', () async {
    final conversation = _FakeConversation()..firstAnswerGate = Completer();
    final audio = _FakeAudio();
    final container = _container(
      conversation: conversation,
      speech: _FakeSpeech(),
      audio: audio,
    );
    final controller = container.read(liveConversationProvider.notifier);

    await controller.start();
    await Future<void>.delayed(const Duration(seconds: 2));
    expect(
      container.read(liveConversationProvider).phase,
      LivePhase.thinking,
    );

    await controller.stop();
    conversation.firstAnswerGate!.complete();
    await Future<void>.delayed(const Duration(milliseconds: 100));

    expect(audio.played, 0);
    expect(container.read(liveConversationProvider).isLive, isFalse);
  });

  test('restarting while an old turn waits runs a single loop', () async {
    final conversation = _FakeConversation()..firstAnswerGate = Completer();
    final audio = _FakeAudio();
    final container = _container(
      conversation: conversation,
      speech: _FakeSpeech(),
      audio: audio,
    );
    final controller = container.read(liveConversationProvider.notifier);

    await controller.start();
    await Future<void>.delayed(const Duration(seconds: 2));
    await controller.stop();
    await controller.start();
    conversation.firstAnswerGate!.complete();
    await Future<void>.delayed(const Duration(milliseconds: 100));

    // The old turn's answer is dropped; the new turn is still listening.
    expect(audio.played, 0);
    expect(
      container.read(liveConversationProvider).phase,
      LivePhase.listening,
    );
  });

  test('Stop while the microphone is opening closes it again', () async {
    final recorder = _FakeRecorder()..startGate = Completer();
    final container = _container(
      conversation: _FakeConversation(),
      speech: _FakeSpeech(),
      audio: _FakeAudio(),
      recorder: recorder,
    );
    final controller = container.read(liveConversationProvider.notifier);

    final starting = controller.start();
    await controller.stop();
    recorder.startGate!.complete();
    await starting;

    expect(recorder.recording, isFalse);
    expect(container.read(liveConversationProvider).isLive, isFalse);
  });
}
