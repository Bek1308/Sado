import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/core/widgets/sado_orb.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/speech/domain/entities/expression_cue.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';

class ConversationView extends ConsumerWidget {
  const ConversationView({super.key});

  static const _bubbleWidthFactor = 0.8;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(conversationControllerProvider);
    final messages = state.messages;
    if (messages.isEmpty && !state.isThinking) return const _Welcome();

    return LayoutBuilder(
      builder: (context, constraints) {
        final maxBubbleWidth = constraints.maxWidth * _bubbleWidthFactor;
        // Newest first, so the list stays pinned to the latest message.
        final items = <Widget>[
          if (state.isThinking) const _ThinkingBubble(),
          for (final message in messages.reversed)
            _Bubble(message: message, maxWidth: maxBubbleWidth),
        ];

        return ListView.separated(
          reverse: true,
          padding: const EdgeInsets.all(AppSpacing.lg),
          itemCount: items.length,
          separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
          itemBuilder: (context, index) => items[index],
        );
      },
    );
  }
}

class _Welcome extends StatelessWidget {
  const _Welcome();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final languages = SpokenLanguage.values
        .map((language) => language.nativeName)
        .join(' · ');

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xxl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SadoOrb(size: 96, glow: true),
            const SizedBox(height: AppSpacing.xxl),
            Text(
              'One voice. Every language.',
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Tap the mic and talk to Sado, or type a message.',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              languages,
              style: theme.textTheme.labelLarge?.copyWith(
                color: theme.colorScheme.primary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _Bubble extends ConsumerWidget {
  const _Bubble({required this.message, required this.maxWidth});

  final ChatMessage message;
  final double maxWidth;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final fromUser = message.speaker == ChatSpeaker.user;
    const round = Radius.circular(AppRadius.lg);
    const tail = Radius.circular(AppRadius.tail);

    return Align(
      alignment: fromUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: maxWidth),
        decoration: BoxDecoration(
          color: fromUser ? colors.primary : colors.surfaceContainerHigh,
          borderRadius: BorderRadius.only(
            topLeft: round,
            topRight: round,
            bottomLeft: fromUser ? round : tail,
            bottomRight: fromUser ? tail : round,
          ),
        ),
        child: Padding(
          padding: EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.md,
            fromUser ? AppSpacing.lg : AppSpacing.xs,
            fromUser ? AppSpacing.md : AppSpacing.xs,
          ),
          child: fromUser
              ? Text(
                  message.text,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: colors.onPrimary,
                  ),
                )
              : Row(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Flexible(
                      child: Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                        child: Text(
                          ExpressionCue.withoutCues(message.text),
                          style: theme.textTheme.bodyLarge,
                        ),
                      ),
                    ),
                    IconButton(
                      tooltip: 'Play again',
                      visualDensity: VisualDensity.compact,
                      iconSize: 20,
                      color: colors.onSurfaceVariant,
                      icon: const Icon(Icons.volume_up_outlined),
                      onPressed: () => ref
                          .read(speakControllerProvider.notifier)
                          .say(message.text),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}

class _ThinkingBubble extends StatefulWidget {
  const _ThinkingBubble();

  @override
  State<_ThinkingBubble> createState() => _ThinkingBubbleState();
}

class _ThinkingBubbleState extends State<_ThinkingBubble>
    with SingleTickerProviderStateMixin {
  static const _dotCount = 3;
  static const _dotSize = 8.0;

  late final _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// Each dot peaks a third of a cycle after the previous one.
  double _opacity(int dot) {
    final phase = (_controller.value - dot / _dotCount) % 1;
    return 0.3 + 0.7 * (1 - (phase * 2 - 1).abs());
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Semantics(
      label: 'Sado is thinking',
      child: Align(
        alignment: Alignment.centerLeft,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: colors.surfaceContainerHigh,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(AppRadius.lg),
              topRight: Radius.circular(AppRadius.lg),
              bottomRight: Radius.circular(AppRadius.lg),
              bottomLeft: Radius.circular(AppRadius.tail),
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.lg,
              vertical: AppSpacing.lg,
            ),
            child: AnimatedBuilder(
              animation: _controller,
              builder: (context, _) => Row(
                mainAxisSize: MainAxisSize.min,
                spacing: AppSpacing.xs,
                children: [
                  for (var dot = 0; dot < _dotCount; dot++)
                    Opacity(
                      opacity: _opacity(dot),
                      child: Container(
                        width: _dotSize,
                        height: _dotSize,
                        decoration: BoxDecoration(
                          color: colors.onSurfaceVariant,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
