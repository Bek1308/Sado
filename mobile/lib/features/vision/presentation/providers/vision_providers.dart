import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/camera/photo_picker.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';
import 'package:sado/features/vision/data/datasources/explanation_remote_data_source.dart';
import 'package:sado/features/vision/data/repositories/explanation_repository_impl.dart';
import 'package:sado/features/vision/domain/repositories/explanation_repository.dart';
import 'package:sado/features/vision/domain/usecases/explain_photograph.dart';

final explanationRepositoryProvider = Provider<ExplanationRepository>(
  (ref) => ExplanationRepositoryImpl(
    ExplanationRemoteDataSource(ref.watch(httpClientProvider)),
  ),
);

final explainPhotographProvider = Provider<ExplainPhotograph>(
  (ref) => ExplainPhotograph(ref.watch(explanationRepositoryProvider)),
);

final visionControllerProvider =
    NotifierProvider<VisionController, VisionState>(
      VisionController.new,
    );

sealed class VisionState {
  const VisionState();
}

final class VisionIdle extends VisionState {
  const VisionIdle();
}

final class VisionExplaining extends VisionState {
  const VisionExplaining();
}

final class VisionExplained extends VisionState {
  const VisionExplained(this.text);

  final String text;
}

final class VisionFailed extends VisionState {
  const VisionFailed(this.message);

  final String message;
}

class VisionController extends Notifier<VisionState> {
  @override
  VisionState build() => const VisionIdle();

  Future<void> explain() async {
    final Photograph? photo;
    try {
      photo = await ref.read(photoPickerProvider).takePhoto();
    } on Exception {
      state = const VisionFailed('Could not open the camera');
      return;
    }
    if (photo == null) {
      state = const VisionIdle();
      return;
    }

    state = const VisionExplaining();
    final result = await ref
        .read(explainPhotographProvider)
        .call(photo, ref.read(spokenLanguageProvider));
    state = switch (result) {
      Ok(:final value) => VisionExplained(value),
      Err(:final failure) => VisionFailed(failure.message),
    };
  }
}
