import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/conversation/presentation/widgets/action_confirmation.dart';
import 'package:sado/features/conversation/presentation/widgets/sado_sphere.dart';
import 'package:sado/features/speech/domain/entities/expression_cue.dart';

/// The whole screen during a hands-free conversation: Sado's sphere in the
/// middle, what it is doing, the last words said, and a way to stop.
class LiveStage extends ConsumerWidget {
  const LiveStage({super.key});

  static const _night = [
    Color(0xFF050B1F),
    Color(0xFF0A1640),
    Color(0xFF1A0F3D),
  ];
  static const _fade = Duration(milliseconds: 300);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final phase = ref.watch(liveConversationProvider).phase;
    final messages = ref.watch(
      conversationControllerProvider.select((state) => state.messages),
    );
    final heard = messages.lastWhereOrNull(
      (m) => m.speaker == ChatSpeaker.user,
    );
    final said =
        messages.isNotEmpty && messages.last.speaker == ChatSpeaker.sado
        ? messages.last
        : null;
    final status = switch (phase) {
      LivePhase.listening => 'Listening',
      LivePhase.thinking => 'Thinking',
      LivePhase.speaking => 'Speaking',
      LivePhase.idle => '',
    };

    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: _night,
        ),
      ),
      child: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final sphere = (constraints.maxWidth * 0.82).clamp(220.0, 420.0);
            return Column(
              children: [
                const SizedBox(height: AppSpacing.xl),
                AnimatedSwitcher(
                  duration: _fade,
                  child: _StatusPill(key: ValueKey(status), label: status),
                ),
                Expanded(
                  child: Center(child: SadoSphere(size: sphere)),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.xl,
                  ),
                  child: AnimatedSwitcher(
                    duration: _fade,
                    child: _Caption(
                      key: ValueKey(said?.text ?? heard?.text),
                      heard: heard?.text,
                      said: said == null
                          ? null
                          : ExpressionCue.withoutCues(said.text),
                      style: theme.textTheme,
                    ),
                  ),
                ),
                const ActionConfirmation(),
                Padding(
                  padding: const EdgeInsets.all(AppSpacing.xl),
                  child: _StopButton(
                    onPressed: () =>
                        ref.read(liveConversationProvider.notifier).stop(),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label, super.key});

  final String label;

  @override
  Widget build(BuildContext context) {
    if (label.isEmpty) return const SizedBox(height: 36);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
          color: Colors.white.withValues(alpha: 0.85),
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}

/// What the user just said, small, and Sado's answer, large.
class _Caption extends StatelessWidget {
  const _Caption({
    required this.heard,
    required this.said,
    required this.style,
    super.key,
  });

  final String? heard;
  final String? said;
  final TextTheme style;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 96),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        spacing: AppSpacing.sm,
        children: [
          if (heard case final text?)
            Text(
              text,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: style.bodyMedium?.copyWith(
                color: Colors.white.withValues(alpha: 0.55),
              ),
            ),
          if (said case final text?)
            Text(
              text,
              maxLines: 4,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: style.titleMedium?.copyWith(
                color: Colors.white,
                height: 1.35,
              ),
            ),
        ],
      ),
    );
  }
}

class _StopButton extends StatelessWidget {
  const _StopButton({required this.onPressed});

  final VoidCallback onPressed;

  static const _size = 68.0;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: 'End conversation',
      child: Material(
        color: const Color(0xFFFF3B30),
        shape: const CircleBorder(),
        elevation: 6,
        shadowColor: const Color(0xFFFF3B30),
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: onPressed,
          child: const SizedBox.square(
            dimension: _size,
            child: Icon(Icons.close_rounded, color: Colors.white, size: 32),
          ),
        ),
      ),
    );
  }
}

extension<T> on List<T> {
  T? lastWhereOrNull(bool Function(T) test) {
    for (var i = length - 1; i >= 0; i--) {
      if (test(this[i])) return this[i];
    }
    return null;
  }
}
