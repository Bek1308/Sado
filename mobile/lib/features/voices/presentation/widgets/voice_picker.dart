import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';
import 'package:sado/features/voices/presentation/providers/voice_providers.dart';

class VoicePicker extends ConsumerWidget {
  const VoicePicker({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return switch (ref.watch(voicesProvider)) {
      AsyncData(value: Ok(:final value)) when value.isNotEmpty => _VoiceList(
        voices: value,
      ),
      AsyncData() || AsyncError() => _Unavailable(
        onRetry: () => ref.invalidate(voicesProvider),
      ),
      _ => const LinearProgressIndicator(),
    };
  }
}

class _VoiceList extends ConsumerWidget {
  const _VoiceList({required this.voices});

  final List<VoiceOption> voices;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId =
        ref.watch(selectedVoiceIdProvider) ??
        voices
            .firstWhere((voice) => voice.isDefault, orElse: () => voices.first)
            .id;

    return Column(
      spacing: AppSpacing.sm,
      children: [
        for (final voice in voices)
          _VoiceTile(
            voice: voice,
            selected: voice.id == selectedId,
            onTap: () =>
                ref.read(selectedVoiceIdProvider.notifier).selected = voice.id,
          ),
      ],
    );
  }
}

class _VoiceTile extends StatelessWidget {
  const _VoiceTile({
    required this.voice,
    required this.selected,
    required this.onTap,
  });

  final VoiceOption voice;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final shape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppRadius.md),
      side: BorderSide(
        color: selected ? colors.primary : colors.outlineVariant,
      ),
    );

    return ListTile(
      shape: shape,
      selected: selected,
      selectedColor: colors.primary,
      selectedTileColor: colors.primary.withValues(alpha: 0.08),
      leading: CircleAvatar(
        backgroundColor: selected
            ? colors.primary
            : colors.surfaceContainerHighest,
        foregroundColor: selected ? colors.onPrimary : colors.onSurfaceVariant,
        child: Text(voice.name.characters.first),
      ),
      title: Text(voice.name),
      subtitle: voice.description.isEmpty ? null : Text(voice.description),
      trailing: selected ? const Icon(Icons.check_circle) : null,
      onTap: onTap,
    );
  }
}

class _Unavailable extends StatelessWidget {
  const _Unavailable({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      children: [
        Expanded(
          child: Text(
            'Voices could not be loaded.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ),
        TextButton(onPressed: onRetry, child: const Text('Retry')),
      ],
    );
  }
}
