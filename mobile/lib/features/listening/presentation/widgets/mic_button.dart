import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';

/// Starts a hands-free conversation with Sado; tap again to stop it.
class MicButton extends ConsumerWidget {
  const MicButton({super.key});

  static const size = 48.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final live = ref.watch(liveConversationProvider);
    final controller = ref.read(liveConversationProvider.notifier);
    final colors = Theme.of(context).colorScheme;

    if (!live.isLive) {
      return SizedBox.square(
        dimension: size,
        child: IconButton.filled(
          tooltip: 'Talk to Sado',
          icon: const Icon(Icons.mic_rounded),
          onPressed: controller.start,
        ),
      );
    }
    return SizedBox.square(
      dimension: size,
      child: _Pulse(
        color: colors.error,
        child: IconButton.filled(
          tooltip: 'Stop',
          style: IconButton.styleFrom(
            backgroundColor: colors.error,
            foregroundColor: colors.onError,
          ),
          icon: const Icon(Icons.stop_rounded),
          onPressed: controller.stop,
        ),
      ),
    );
  }
}

/// A soft ring that breathes around the button while Sado is live.
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
