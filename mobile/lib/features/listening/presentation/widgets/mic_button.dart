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

  static const size = 48.0;
  static const _progressSize = 20.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(listeningControllerProvider, (_, state) {
      if (state is ListeningHeard) onHeard(state.text);
    });
    final colors = Theme.of(context).colorScheme;
    final state = ref.watch(listeningControllerProvider);
    final controller = ref.read(listeningControllerProvider.notifier);

    return SizedBox.square(
      dimension: size,
      child: switch (state) {
        ListeningRecording() => _Pulse(
          color: colors.error,
          child: IconButton.filled(
            tooltip: 'Stop listening',
            style: IconButton.styleFrom(
              backgroundColor: colors.error,
              foregroundColor: colors.onError,
            ),
            icon: const Icon(Icons.stop_rounded),
            onPressed: () => controller.stop(language),
          ),
        ),
        ListeningTranscribing() => const Center(
          child: SizedBox.square(
            dimension: _progressSize,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
        _ => IconButton.filled(
          tooltip: 'Talk to Sado',
          icon: const Icon(Icons.mic_rounded),
          onPressed: controller.start,
        ),
      },
    );
  }
}

/// A soft ring that breathes around the button while the mic is open.
class _Pulse extends StatefulWidget {
  const _Pulse({required this.color, required this.child});

  final Color color;
  final Widget child;

  @override
  State<_Pulse> createState() => _PulseState();
}

class _PulseState extends State<_Pulse> with SingleTickerProviderStateMixin {
  static const _maxRingWidth = 8.0;

  late final _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1100),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => DecoratedBox(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: widget.color.withValues(alpha: 0.3),
              spreadRadius: _maxRingWidth * _controller.value,
            ),
          ],
        ),
        child: child,
      ),
      child: widget.child,
    );
  }
}
