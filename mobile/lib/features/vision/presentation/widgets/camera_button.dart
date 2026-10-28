import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/vision/presentation/providers/vision_providers.dart';

/// Captures a paper with the camera; its explanation arrives through
/// [onExplained].
class CameraButton extends ConsumerWidget {
  const CameraButton({
    required this.language,
    required this.onExplained,
    super.key,
  });

  final SpokenLanguage language;
  final ValueChanged<String> onExplained;

  static const size = 48.0;
  static const _progressSize = 20.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(visionControllerProvider, (_, state) {
      if (state is VisionExplained) onExplained(state.text);
    });
    final explaining = ref.watch(visionControllerProvider) is VisionExplaining;
    final controller = ref.read(visionControllerProvider.notifier);

    return SizedBox.square(
      dimension: size,
      child: explaining
          ? const Center(
              child: SizedBox.square(
                dimension: _progressSize,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          : IconButton.filledTonal(
              tooltip: 'Photograph a paper',
              icon: const Icon(Icons.camera_alt_outlined),
              onPressed: () => controller.explain(language),
            ),
    );
  }
}
