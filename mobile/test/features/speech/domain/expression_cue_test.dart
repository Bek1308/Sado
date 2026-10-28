import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/speech/domain/entities/expression_cue.dart';

void main() {
  test('hides cues from the text a person reads', () {
    expect(
      ExpressionCue.withoutCues('Voy! [surprise] Rostdanmi? [laugh]'),
      'Voy! Rostdanmi?',
    );
    expect(ExpressionCue.withoutCues('Mayli [sigh].'), 'Mayli.');
  });

  test('leaves ordinary brackets alone', () {
    expect(ExpressionCue.withoutCues('Bob [2] tayyor'), 'Bob [2] tayyor');
  });
}
