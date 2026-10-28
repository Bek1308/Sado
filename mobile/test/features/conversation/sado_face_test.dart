import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/conversation/presentation/widgets/sado_face.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

final class _FixedMood extends MoodSetting {
  _FixedMood(this._mood);

  final Mood _mood;

  @override
  Mood build() => _mood;
}

void main() {
  // Explicit pumps: the face breathes forever, so pumpAndSettle would hang.
  testWidgets('shows every mood without crashing', (tester) async {
    for (final mood in Mood.values) {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [moodProvider.overrideWith(() => _FixedMood(mood))],
          child: const MaterialApp(
            home: Scaffold(body: SadoFace()),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 500));

      expect(find.byType(SadoFace), findsOneWidget);
    }
  });
}
