import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';

void main() {
  test('turns microphone decibels into a 0 to 1 level', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    double levelFor(double decibels) {
      container.read(micLevelProvider.notifier).hear(decibels);
      return container.read(micLevelProvider);
    }

    expect(levelFor(-160), 0);
    expect(levelFor(-32.5), closeTo(0.5, 0.01));
    expect(levelFor(0), 1);

    container.read(micLevelProvider.notifier).quiet();
    expect(container.read(micLevelProvider), 0);
  });
}
