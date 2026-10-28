import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_settings_providers.dart';

/// Picks how Sado talks: at home, in person, at work, or on the go.
class ModeSwitcher extends ConsumerWidget {
  const ModeSwitcher({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(sadoModeProvider);
    return SegmentedButton<SadoMode>(
      segments: [
        for (final value in SadoMode.values)
          ButtonSegment(value: value, label: Text(value.label)),
      ],
      selected: {mode},
      showSelectedIcon: false,
      onSelectionChanged: (selected) =>
          ref.read(sadoModeProvider.notifier).selected = selected.first,
    );
  }
}
