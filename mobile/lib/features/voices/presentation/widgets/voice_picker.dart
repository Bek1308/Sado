import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';
import 'package:sado/features/voices/presentation/providers/voice_providers.dart';

class VoicePicker extends ConsumerWidget {
  const VoicePicker({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final voices = switch (ref.watch(voicesProvider)) {
      AsyncData(value: Ok(:final value)) => value,
      _ => const <VoiceOption>[],
    };
    if (voices.isEmpty) return const SizedBox.shrink();

    final selectedId =
        ref.watch(selectedVoiceIdProvider) ??
        voices
            .firstWhere((voice) => voice.isDefault, orElse: () => voices.first)
            .id;

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final voice in voices)
          ChoiceChip(
            avatar: const Icon(Icons.record_voice_over, size: 18),
            label: Text(voice.name),
            selected: voice.id == selectedId,
            onSelected: (_) =>
                ref.read(selectedVoiceIdProvider.notifier).selected = voice.id,
          ),
      ],
    );
  }
}
