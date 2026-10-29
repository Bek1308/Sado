import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/router/app_router.dart';
import 'package:sado/core/storage/preferences.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';
import 'package:sado/features/server_status/presentation/providers/server_status_providers.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';
import 'package:sado/features/voices/presentation/providers/voice_providers.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<SharedPreferences> _preferences(Map<String, Object> values) async {
  SharedPreferences.setMockInitialValues(values);
  return SharedPreferences.getInstance();
}

Future<void> _pumpApp(
  WidgetTester tester,
  SharedPreferences preferences,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        sharedPreferencesProvider.overrideWithValue(preferences),
        serverStatusProvider.overrideWith(
          (ref) async => const Ok(ServerStatus(name: 'Sado', version: '1')),
        ),
        voicesProvider.overrideWith(
          (ref) async => const Ok(<VoiceOption>[]),
        ),
      ],
      child: Consumer(
        builder: (context, ref, _) =>
            MaterialApp.router(routerConfig: ref.watch(appRouterProvider)),
      ),
    ),
  );
  await _settle(tester);
}

/// Sado's face animates forever, so pumpAndSettle would never return.
Future<void> _settle(WidgetTester tester) async {
  for (var frame = 0; frame < 10; frame++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

void main() {
  testWidgets('introduces Sado once, then opens the conversation', (
    tester,
  ) async {
    final preferences = await _preferences({});
    await _pumpApp(tester, preferences);

    expect(find.text('Talk in your own language'), findsOneWidget);

    await tester.tap(find.text('Next'));
    await _settle(tester);
    await tester.tap(find.text('Next'));
    await _settle(tester);
    expect(find.text('Any paper, explained'), findsOneWidget);

    await tester.tap(find.text('Start talking'));
    await _settle(tester);

    expect(find.text('One voice. Every language.'), findsOneWidget);
    expect(preferences.getBool('onboarding_done'), isTrue);
  });

  testWidgets('goes straight to the conversation after the first time', (
    tester,
  ) async {
    await _pumpApp(tester, await _preferences({'onboarding_done': true}));

    expect(find.text('Talk in your own language'), findsNothing);
    expect(find.text('One voice. Every language.'), findsOneWidget);
  });
}
