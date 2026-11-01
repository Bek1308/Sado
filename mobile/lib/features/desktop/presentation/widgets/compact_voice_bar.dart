import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/core/widgets/sado_orb.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_settings_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/conversation/presentation/widgets/voice_wave.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

/// All Sado shows while talking from the tray: its mark, the live voice wave
/// and one line saying what it is doing. When it needs a yes, the bar grows
/// just enough to ask.
class CompactVoiceBar extends ConsumerWidget {
  const CompactVoiceBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final pending = ref.watch(
      conversationControllerProvider.select(
        (state) => state.lastReply?.pendingAction,
      ),
    );

    // Windows cannot show a see-through window here, so the bar fills its
    // window edge to edge and the system rounds the corners.
    return Material(
      color: colors.surfaceContainerHigh,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.lg,
            vertical: AppSpacing.md,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            spacing: AppSpacing.md,
            children: [
              Row(
                spacing: AppSpacing.md,
                children: [
                  const SadoOrb(),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const VoiceWave(height: 28),
                        Text(
                          _status(ref),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: colors.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Above the app's navigator there is no overlay for a
                  // tooltip, so the label is only spoken by screen readers.
                  IconButton(
                    icon: const Icon(
                      Icons.close_rounded,
                      semanticLabel: 'Stop',
                    ),
                    onPressed: () =>
                        ref.read(liveConversationProvider.notifier).stop(),
                  ),
                ],
              ),
              if (pending != null) _Ask(description: pending.description),
            ],
          ),
        ),
      ),
    );
  }

  String _status(WidgetRef ref) {
    final phase = ref.watch(liveConversationProvider).phase;
    final thinking = ref.watch(
      conversationControllerProvider.select((state) => state.isThinking),
    );
    final speaking = ref.watch(speakControllerProvider).isLoading;
    final lastWords = ref.watch(
      conversationControllerProvider.select((state) => state.lastReply?.text),
    );
    return switch ((phase, thinking, speaking)) {
      (LivePhase.listening, _, _) => 'Listening…',
      (_, true, _) || (LivePhase.thinking, _, _) => 'Thinking…',
      (_, _, true) || (LivePhase.speaking, _, _) => lastWords ?? 'Speaking…',
      _ => lastWords ?? 'Sado',
    };
  }
}

class _Ask extends ConsumerWidget {
  const _Ask({required this.description});

  final String description;

  Future<void> _answer(WidgetRef ref, {required bool yes}) async {
    final reply = await ref
        .read(conversationControllerProvider.notifier)
        .answer(
          yes: yes,
          language: ref.read(spokenLanguageProvider),
          mode: ref.read(sadoModeProvider),
        );
    if (reply != null) {
      await ref.read(speakControllerProvider.notifier).say(reply.text);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: AppSpacing.sm,
      children: [
        Text(
          description,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: theme.textTheme.bodyMedium,
        ),
        Row(
          spacing: AppSpacing.sm,
          children: [
            Expanded(
              child: Text(
                'Say yes or no, or tap',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ),
            OutlinedButton(
              onPressed: () => _answer(ref, yes: false),
              child: const Text('No'),
            ),
            FilledButton(
              onPressed: () => _answer(ref, yes: true),
              child: const Text('Yes'),
            ),
          ],
        ),
      ],
    );
  }
}
