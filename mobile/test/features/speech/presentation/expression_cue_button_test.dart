import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/speech/presentation/widgets/expression_cue_button.dart';

void main() {
  testWidgets('inserts the chosen cue at the cursor', (tester) async {
    final controller = TextEditingController(text: 'Voy!Rostdanmi?')
      ..selection = const TextSelection.collapsed(offset: 4);
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ExpressionCueButton(controller: controller)),
      ),
    );
    await tester.tap(find.byTooltip('Add an expression'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Surprise'));
    await tester.pumpAndSettle();

    expect(controller.text, 'Voy! [surprise] Rostdanmi?');
    expect(controller.selection.baseOffset, 'Voy! [surprise] '.length);
  });
}
