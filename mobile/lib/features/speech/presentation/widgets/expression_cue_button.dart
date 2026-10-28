import 'package:flutter/material.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/speech/domain/entities/expression_cue.dart';

/// Inserts an expression cue at the cursor so Sado performs it while speaking.
class ExpressionCueButton extends StatelessWidget {
  const ExpressionCueButton({required this.controller, super.key});

  final TextEditingController controller;

  void _insert(ExpressionCue cue) {
    final selection = controller.selection;
    final text = controller.text;
    final start = selection.isValid ? selection.start : text.length;
    final end = selection.isValid ? selection.end : text.length;
    final inserted = ' ${cue.tag} ';

    controller.value = TextEditingValue(
      text: text.replaceRange(start, end, inserted),
      selection: TextSelection.collapsed(offset: start + inserted.length),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<ExpressionCue>(
      tooltip: 'Add an expression',
      icon: const Icon(Icons.add_reaction_outlined),
      position: PopupMenuPosition.over,
      onSelected: _insert,
      itemBuilder: (context) => [
        for (final cue in ExpressionCue.values)
          PopupMenuItem(
            value: cue,
            child: Row(
              spacing: AppSpacing.md,
              children: [Text(cue.emoji), Text(cue.label)],
            ),
          ),
      ],
    );
  }
}
