import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/record_voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/listening/data/datasources/transcription_remote_data_source.dart';
import 'package:sado/features/listening/data/repositories/transcription_repository_impl.dart';
import 'package:sado/features/listening/domain/repositories/transcription_repository.dart';
import 'package:sado/features/listening/domain/usecases/transcribe_recording.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

final transcriptionRepositoryProvider = Provider<TranscriptionRepository>(
  (ref) => TranscriptionRepositoryImpl(
    TranscriptionRemoteDataSource(ref.watch(httpClientProvider)),
  ),
);

final transcribeRecordingProvider = Provider<TranscribeRecording>(
  (ref) => TranscribeRecording(ref.watch(transcriptionRepositoryProvider)),
);

final listeningControllerProvider =
    NotifierProvider<ListeningController, ListeningState>(
      ListeningController.new,
    );

sealed class ListeningState {
  const ListeningState();
}

final class ListeningIdle extends ListeningState {
  const ListeningIdle();
}

final class ListeningRecording extends ListeningState {
  const ListeningRecording();
}

final class ListeningTranscribing extends ListeningState {
  const ListeningTranscribing();
}

final class ListeningHeard extends ListeningState {
  const ListeningHeard(this.text, this.language);

  final String text;
  final SpokenLanguage language;
}

final class ListeningFailed extends ListeningState {
  const ListeningFailed(this.message);

  final String message;
}

class ListeningController extends Notifier<ListeningState> {
  @override
  ListeningState build() => const ListeningIdle();

  Future<void> start() async {
    final started = await ref.read(voiceRecorderProvider).start();
    state = started
        ? const ListeningRecording()
        : const ListeningFailed('Microphone access was denied');
  }

  /// Turns the microphone off and throws the recording away unheard.
  Future<void> cancel() async {
    await ref.read(voiceRecorderProvider).stop();
    state = const ListeningIdle();
  }

  Future<void> stop() async {
    final recording = await ref.read(voiceRecorderProvider).stop();
    if (recording == null) {
      state = const ListeningIdle();
      return;
    }

    state = const ListeningTranscribing();
    final result = await ref.read(transcribeRecordingProvider).call(recording);
    final heard = switch (result) {
      Ok(:final value) => ListeningHeard(value.text, value.language),
      Err(:final failure) => ListeningFailed(failure.message),
    };
    state = heard;
    if (heard is ListeningHeard) {
      ref.read(spokenLanguageProvider.notifier).current = heard.language;
    }
  }
}

/// How loud the user is speaking right now, from 0 to 1, so Sado's face can
/// show it is listening.
final micLevelProvider = NotifierProvider<MicLevel, double>(MicLevel.new);

class MicLevel extends Notifier<double> {
  /// Below this the room is quiet; above the ceiling the user is loud.
  static const _floorDb = -50.0;
  static const _ceilingDb = -15.0;

  @override
  double build() => 0;

  void hear(double decibels) =>
      state = ((decibels - _floorDb) / (_ceilingDb - _floorDb)).clamp(0.0, 1.0);

  void quiet() => state = 0;
}
