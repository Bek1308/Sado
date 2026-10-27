import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/home/presentation/pages/home_page.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';
import 'package:sado/features/server_status/presentation/providers/server_status_providers.dart';

Future<void> _pumpHomePage(
  WidgetTester tester,
  Result<ServerStatus> status,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [serverStatusProvider.overrideWith((ref) async => status)],
      child: const MaterialApp(home: HomePage()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows the server version when connected', (tester) async {
    await _pumpHomePage(
      tester,
      const Ok(ServerStatus(name: 'Sado', version: '0.1.0')),
    );

    expect(find.text('Sado'), findsOneWidget);
    expect(find.text('Connected · v0.1.0'), findsOneWidget);
  });

  testWidgets('shows the failure message when offline', (tester) async {
    await _pumpHomePage(
      tester,
      const Err(NetworkFailure('Server is unreachable')),
    );

    expect(find.text('Server is unreachable'), findsOneWidget);
  });
}
