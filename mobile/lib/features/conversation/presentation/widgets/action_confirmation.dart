import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_settings_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

/// Shows what Sado wants to do on the computer, with Yes and No. Saying the
/// answer works just as well; this is for the times typing or tapping is
/// easier.
class ActionConfirmation extends ConsumerWidget {
  const ActionConfirmation({super.key});

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
    final pending = ref.watch(
      conversationControllerProvider.select(
        (state) => state.lastReply?.pendingAction,
      ),
    );
    final busy = ref.watch(
      conversationControllerProvider.select((state) => state.isThinking),
    );
    if (pending == null) return const SizedBox.shrink();

    final theme = Theme.of(context);
    final colors = theme.colorScheme;

    return Card.filled(
      color: colors.primaryContainer,
      margin: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.sm,
        AppSpacing.md,
        0,
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: AppSpacing.md,
          children: [
            Row(
              spacing: AppSpacing.sm,
              children: [
                Icon(Icons.computer_rounded, color: colors.onPrimaryContainer),
                Text(
                  'Sado asks before acting',
                  style: theme.textTheme.labelLarge?.copyWith(
                    color: colors.onPrimaryContainer,
                  ),
                ),
              ],
            ),
            Text(
              pending.description,
              style: theme.textTheme.bodyLarge?.copyWith(
                color: colors.onPrimaryContainer,
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              spacing: AppSpacing.sm,
              children: [
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: colors.onPrimaryContainer,
                    side: BorderSide(color: colors.onPrimaryContainer),
                  ),
                  onPressed: busy ? null : () => _answer(ref, yes: false),
                  child: const Text('No'),
                ),
                FilledButton.icon(
                  onPressed: busy ? null : () => _answer(ref, yes: true),
                  icon: const Icon(Icons.check_rounded),
                  label: const Text('Yes, do it'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
