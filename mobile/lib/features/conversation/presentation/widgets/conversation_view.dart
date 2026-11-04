import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/desktop/desktop_host.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/core/theme/app_theme.dart';
import 'package:sado/core/widgets/sado_orb.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/widgets/sado_sphere.dart';
import 'package:sado/features/conversation/presentation/widgets/starter_prompts.dart';
import 'package:sado/features/memory/presentation/providers/memory_providers.dart';
import 'package:sado/features/speech/domain/entities/expression_cue.dart';
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

class _Welcome extends ConsumerWidget {
  const _Welcome();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    // On a computer the stage above already shows Sado's face.
    final showFace = !ref.watch(isDesktopProvider);

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xxl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (showFace) ...[
              const SadoSphere(size: 220),
              const SizedBox(height: AppSpacing.md),
            ],
            ShaderMask(
              shaderCallback: (bounds) => const LinearGradient(
                colors: AppTheme.brandGradient,
              ).createShader(bounds),
              child: Text(
                "Hi, I'm Sado",
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Talk in your own language. I listen, act and remember.',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.xl),
            const StarterPrompts(),
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

    final bubble = GestureDetector(
      onLongPress: () => _showActions(context, ref),
      child: Container(
        constraints: BoxConstraints(maxWidth: maxWidth),
        decoration: BoxDecoration(
          color: fromUser ? null : colors.surfaceContainerHigh,
          gradient: fromUser
              ? const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: AppTheme.brandGradient,
                )
              : null,
          boxShadow: fromUser
              ? [
                  BoxShadow(
                    color: AppTheme.brandGradient.first.withValues(
                      alpha: 0.25,
                    ),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
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

    if (fromUser) {
      return Align(alignment: Alignment.centerRight, child: bubble);
    }
    // Sado's words come with its mark, like a name beside a message.
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      spacing: AppSpacing.sm,
      children: [
        const SadoOrb(size: 28),
        Flexible(child: bubble),
      ],
    );
  }

  Future<void> _showActions(BuildContext context, WidgetRef ref) async {
    final text = ExpressionCue.withoutCues(message.text);
    final action = await showModalBottomSheet<_BubbleAction>(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (message.speaker == ChatSpeaker.user)
              ListTile(
                leading: const Icon(Icons.bookmark_add_outlined),
                title: const Text('Remember this'),
                subtitle: const Text('Sado will keep it in Memories'),
                onTap: () => Navigator.of(context).pop(_BubbleAction.remember),
              ),
            ListTile(
              leading: const Icon(Icons.copy_outlined),
              title: const Text('Copy text'),
              onTap: () => Navigator.of(context).pop(_BubbleAction.copy),
            ),
          ],
        ),
      ),
    );
    if (action == null || !context.mounted) return;

    final messenger = ScaffoldMessenger.of(context);
    final note = switch (action) {
      _BubbleAction.remember =>
        await ref.read(memoriesControllerProvider.notifier).remember(text) ??
            'Sado will remember this.',
      _BubbleAction.copy => await Clipboard.setData(
        ClipboardData(text: text),
      ).then((_) => 'Copied.'),
    };
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(note)));
  }
}

enum _BubbleAction { remember, copy }

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
