import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/home/presentation/pages/home_page.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';
import 'package:sado/features/server_status/presentation/providers/server_status_providers.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';
import 'package:sado/features/voices/presentation/providers/voice_providers.dart';

const Result<ServerStatus> _online = Ok(
  ServerStatus(name: 'Sado', version: '0.1.0'),
);

const _voices = [
  VoiceOption(id: 'sado', name: 'Sado', isDefault: true),
  VoiceOption(
    id: 'opa',
    name: 'Opa',
    description: 'Warm and bright',
    isDefault: false,
  ),
];

Future<void> _pumpHomePage(
  WidgetTester tester,
  Result<ServerStatus> status,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        serverStatusProvider.overrideWith((ref) async => status),
        voicesProvider.overrideWith((ref) async => const Ok(_voices)),
      ],
      child: const MaterialApp(home: HomePage()),
    ),
  );
  await tester.pumpAndSettle();
}

ListTile _voice(WidgetTester tester, String name) =>
    tester.widget<ListTile>(find.widgetWithText(ListTile, name));

void main() {
  testWidgets('welcomes the user and shows that Sado is online', (
    tester,
  ) async {
    await _pumpHomePage(tester, _online);

    expect(find.text('One voice. Every language.'), findsOneWidget);
    expect(find.text('Online'), findsOneWidget);
    expect(find.byTooltip('Talk to Sado'), findsOneWidget);
  });

  testWidgets('explains the problem and offers a retry when offline', (
    tester,
  ) async {
    await _pumpHomePage(
      tester,
      const Err(NetworkFailure('Server is unreachable')),
    );

    expect(find.text('Offline'), findsOneWidget);
    expect(find.text('Server is unreachable'), findsOneWidget);
    expect(find.widgetWithText(TextButton, 'Retry'), findsOneWidget);
  });

  testWidgets('swaps the mic for send once there is text', (tester) async {
    await _pumpHomePage(tester, _online);

    await tester.enterText(find.byType(TextField), 'Salom');
    await tester.pump();

    expect(find.byTooltip('Send'), findsOneWidget);
    expect(find.byTooltip('Talk to Sado'), findsNothing);
  });

  testWidgets('lets the user pick a voice in the style sheet', (tester) async {
    await _pumpHomePage(tester, _online);

    await tester.tap(find.byTooltip('Voice & style'));
    await tester.pumpAndSettle();

    expect(_voice(tester, 'Sado').selected, isTrue);
    expect(_voice(tester, 'Opa').selected, isFalse);
    expect(find.text('Warm and bright'), findsOneWidget);

    await tester.tap(find.widgetWithText(ListTile, 'Opa'));
    await tester.pump();

    expect(_voice(tester, 'Opa').selected, isTrue);
    expect(_voice(tester, 'Sado').selected, isFalse);
  });
}
