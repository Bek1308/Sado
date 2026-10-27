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

const _voices = [
  VoiceOption(id: 'sado', name: 'Sado', isDefault: true),
  VoiceOption(id: 'opa', name: 'Opa', isDefault: false),
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

ChoiceChip _chip(WidgetTester tester, String name) =>
    tester.widget<ChoiceChip>(find.widgetWithText(ChoiceChip, name));

void main() {
  testWidgets('shows the server version when connected', (tester) async {
    await _pumpHomePage(
      tester,
      const Ok(ServerStatus(name: 'Sado', version: '0.1.0')),
    );

    expect(find.text('One voice. Every language.'), findsOneWidget);
    expect(find.text('Connected · v0.1.0'), findsOneWidget);
  });

  testWidgets('shows the failure message when offline', (tester) async {
    await _pumpHomePage(
      tester,
      const Err(NetworkFailure('Server is unreachable')),
    );

    expect(find.text('Server is unreachable'), findsOneWidget);
  });

  testWidgets('preselects the default voice and lets the user switch', (
    tester,
  ) async {
    await _pumpHomePage(
      tester,
      const Ok(ServerStatus(name: 'Sado', version: '0.1.0')),
    );

    expect(_chip(tester, 'Sado').selected, isTrue);
    expect(_chip(tester, 'Opa').selected, isFalse);

    await tester.tap(find.widgetWithText(ChoiceChip, 'Opa'));
    await tester.pump();

    expect(_chip(tester, 'Opa').selected, isTrue);
    expect(_chip(tester, 'Sado').selected, isFalse);
  });
}
