import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

/// The language Sado listens and answers in, always one tap away.
class LanguageMenuButton extends ConsumerWidget {
  const LanguageMenuButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final language = ref.watch(spokenLanguageProvider);

    return PopupMenuButton<SpokenLanguage>(
      tooltip: 'Language',
      initialValue: language,
      position: PopupMenuPosition.under,
      onSelected: (selected) =>
          ref.read(spokenLanguageProvider.notifier).selected = selected,
      itemBuilder: (context) => [
        for (final option in SpokenLanguage.values)
          CheckedPopupMenuItem(
            value: option,
            checked: option == language,
            child: Text(option.nativeName),
          ),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: ShapeDecoration(
          shape: StadiumBorder(
            side: BorderSide(color: theme.colorScheme.outlineVariant),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          spacing: AppSpacing.xs,
          children: [
            Icon(
              Icons.translate,
              size: 18,
              color: theme.colorScheme.onSurfaceVariant,
            ),
            Text(
              language.code.toUpperCase(),
              style: theme.textTheme.labelLarge,
            ),
          ],
        ),
      ),
    );
  }
}
