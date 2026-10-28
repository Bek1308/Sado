import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';
import 'package:sado/features/voices/presentation/widgets/voice_picker.dart';

Future<void> showVoiceStyleSheet(BuildContext context) =>
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const VoiceStyleSheet(),
    );

/// Everything about how Sado sounds, kept out of the conversation itself.
class VoiceStyleSheet extends ConsumerWidget {
  const VoiceStyleSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mood = ref.watch(moodProvider);

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.xl,
        0,
        AppSpacing.xl,
        AppSpacing.xl,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Voice & style', style: Theme.of(context).textTheme.titleLarge),
          const _Section(title: 'Voice', child: VoicePicker()),
          _Section(
            title: 'Mood',
            child: Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                for (final option in Mood.values)
                  ChoiceChip(
                    avatar: Text(option.emoji),
                    label: Text(option.label),
                    selected: option == mood,
                    onSelected: (_) =>
                        ref.read(moodProvider.notifier).selected = option,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.xl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: AppSpacing.md,
        children: [
          Text(
            title,
            style: theme.textTheme.labelLarge?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          child,
        ],
      ),
    );
  }
}
