import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/record_voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/listening/data/datasources/transcription_remote_data_source.dart';
import 'package:sado/features/listening/data/repositories/transcription_repository_impl.dart';
import 'package:sado/features/listening/domain/repositories/transcription_repository.dart';
import 'package:sado/features/listening/domain/usecases/transcribe_recording.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

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
  const ListeningHeard(this.text);

  final String text;
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

  Future<void> stop(SpokenLanguage language) async {
    final recording = await ref.read(voiceRecorderProvider).stop();
    if (recording == null) {
      state = const ListeningIdle();
      return;
    }

    state = const ListeningTranscribing();
    final result = await ref
        .read(transcribeRecordingProvider)
        .call(recording, language);
    state = switch (result) {
      Ok(:final value) => ListeningHeard(value),
      Err(:final failure) => ListeningFailed(failure.message),
    };
  }
}
