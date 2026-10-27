import 'package:flutter/material.dart';
import 'package:sado/features/speech/domain/entities/expression_cue.dart';

/// Inserts an expression cue at the cursor so Sado performs it while speaking.
class ExpressionCueBar extends StatelessWidget {
  const ExpressionCueBar({required this.controller, super.key});

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
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final cue in ExpressionCue.values)
          ActionChip(
            avatar: Text(cue.emoji),
            label: Text(cue.label),
            onPressed: () => _insert(cue),
          ),
      ],
    );
  }
}
