import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_settings_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

/// One tap shows what Sado can do: search, lists and reminders.
const Map<SpokenLanguage, List<String>> _prompts = {
  SpokenLanguage.uzbek: [
    'Bugun havo qanday?',
    "Xarid ro'yxatimga non va sut qo'sh",
    "Ertaga soat 9 da shifokorni eslatib qo'y",
  ],
  SpokenLanguage.tajik: [
    'Имрӯз ҳаво чӣ хел аст?',
    'Ба рӯйхати харид нон ва шир илова кун',
    'Пагоҳ соати 9 духтурро хотиррасон кун',
  ],
  SpokenLanguage.russian: [
    'Какая сегодня погода?',
    'Добавь хлеб и молоко в список покупок',
    'Напомни завтра в 9 о враче',
  ],
  SpokenLanguage.english: [
    "What's the weather today?",
    'Add bread and milk to my shopping list',
    'Remind me about the doctor tomorrow at 9',
  ],
};

/// The languages Sado speaks, and a few things to ask it in the chosen one.
class StarterPrompts extends ConsumerWidget {
  const StarterPrompts({super.key});

  Future<void> _ask(WidgetRef ref, String prompt) async {
    final reply = await ref
        .read(conversationControllerProvider.notifier)
        .ask(
          prompt,
          ref.read(spokenLanguageProvider),
          ref.read(sadoModeProvider),
        );
    if (reply != null) {
      await ref.read(speakControllerProvider.notifier).say(reply.text);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final language = ref.watch(spokenLanguageProvider);
    final colors = Theme.of(context).colorScheme;

    return Column(
      spacing: AppSpacing.lg,
      children: [
        Wrap(
          alignment: WrapAlignment.center,
          spacing: AppSpacing.sm,
          runSpacing: AppSpacing.sm,
          children: [
            for (final option in SpokenLanguage.values)
              ChoiceChip(
                label: Text(option.nativeName),
                selected: option == language,
                onSelected: (_) =>
                    ref.read(spokenLanguageProvider.notifier).current = option,
              ),
          ],
        ),
        Column(
          spacing: AppSpacing.sm,
          children: [
            for (final prompt in _prompts[language]!)
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    alignment: Alignment.centerLeft,
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    side: BorderSide(color: colors.outlineVariant),
                  ),
                  icon: const Icon(Icons.north_east_rounded, size: 18),
                  label: Text(prompt),
                  onPressed: () => _ask(ref, prompt),
                ),
              ),
          ],
        ),
      ],
    );
  }
}
