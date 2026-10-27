import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/speech/presentation/widgets/expression_cue_bar.dart';

void main() {
  testWidgets('inserts the cue at the cursor', (tester) async {
    final controller = TextEditingController(text: 'Voy!Rostdanmi?')
      ..selection = const TextSelection.collapsed(offset: 4);
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ExpressionCueBar(controller: controller)),
      ),
    );
    await tester.tap(find.widgetWithText(ActionChip, 'Surprise'));

    expect(controller.text, 'Voy! [surprise] Rostdanmi?');
    expect(controller.selection.baseOffset, 'Voy! [surprise] '.length);
  });
}
