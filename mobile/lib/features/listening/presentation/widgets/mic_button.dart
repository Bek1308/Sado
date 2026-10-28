import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

/// Tap to start listening, tap again to stop; the transcript arrives through
/// [onHeard].
class MicButton extends ConsumerWidget {
  const MicButton({required this.language, required this.onHeard, super.key});

  final SpokenLanguage language;
  final ValueChanged<String> onHeard;

  static const _progressSize = 20.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(listeningControllerProvider, (_, state) {
      if (state is ListeningHeard) onHeard(state.text);
    });
    final state = ref.watch(listeningControllerProvider);
    final controller = ref.read(listeningControllerProvider.notifier);

    return switch (state) {
      ListeningRecording() => IconButton.filled(
        tooltip: 'Stop listening',
        style: IconButton.styleFrom(
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
        icon: const Icon(Icons.stop),
        onPressed: () => controller.stop(language),
      ),
      ListeningTranscribing() => const SizedBox.square(
        dimension: 48,
        child: Center(
          child: SizedBox.square(
            dimension: _progressSize,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      ),
      _ => IconButton.filled(
        tooltip: 'Talk to Sado',
        icon: const Icon(Icons.mic),
        onPressed: controller.start,
      ),
    };
  }
}
