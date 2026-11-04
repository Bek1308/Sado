import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_settings_providers.dart';

/// Picks how Sado talks: at home, in person, at work, or on the go.
class ModeSwitcher extends ConsumerWidget {
  const ModeSwitcher({super.key});

  static const Map<SadoMode, IconData> _icons = {
    SadoMode.home: Icons.home_rounded,
    SadoMode.personal: Icons.favorite_rounded,
    SadoMode.work: Icons.work_rounded,
    SadoMode.onTheGo: Icons.directions_walk_rounded,
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(sadoModeProvider);
    final colors = Theme.of(context).colorScheme;

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        spacing: AppSpacing.sm,
        children: [
          for (final value in SadoMode.values)
            ChoiceChip(
              avatar: Icon(
                _icons[value],
                size: 16,
                color: value == mode ? colors.onPrimary : colors.primary,
              ),
              label: Text(value.label),
              selected: value == mode,
              selectedColor: colors.primary,
              labelStyle: TextStyle(
                color: value == mode ? colors.onPrimary : colors.onSurface,
                fontWeight: FontWeight.w500,
              ),
              side: BorderSide(
                color: value == mode
                    ? Colors.transparent
                    : colors.outlineVariant.withValues(alpha: 0.6),
              ),
              visualDensity: VisualDensity.compact,
              onSelected: (_) =>
                  ref.read(sadoModeProvider.notifier).selected = value,
            ),
        ],
      ),
    );
  }
}
