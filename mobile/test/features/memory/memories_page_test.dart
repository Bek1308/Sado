import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/presentation/pages/memories_page.dart';
import 'package:sado/features/memory/presentation/providers/memory_providers.dart';

import 'fake_memory_repository.dart';

Future<void> _pump(WidgetTester tester, FakeMemoryRepository repository) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [memoryRepositoryProvider.overrideWithValue(repository)],
      child: const MaterialApp(home: MemoriesPage()),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('explains how to add a memory when there are none', (
    tester,
  ) async {
    await _pump(tester, FakeMemoryRepository());

    expect(find.text('Nothing saved yet'), findsOneWidget);
  });

  testWidgets('adds a memory through the dialog', (tester) async {
    await _pump(tester, FakeMemoryRepository());

    await tester.tap(find.text('Add memory'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Ismim Aziz');
    await tester.pump();
    await tester.tap(find.widgetWithText(FilledButton, 'Save'));
    await tester.pumpAndSettle();

    expect(find.text('Ismim Aziz'), findsOneWidget);
    expect(find.text('Saved 28 Oct 2026'), findsOneWidget);
  });

  testWidgets('forgets a memory with the delete button', (tester) async {
    final repository = FakeMemoryRepository([
      Memory(id: 'name', text: 'Ismim Aziz', createdAt: DateTime(2026, 10, 27)),
    ]);
    await _pump(tester, repository);

    await tester.tap(find.byTooltip('Forget'));
    await tester.pumpAndSettle();

    expect(find.text('Ismim Aziz'), findsNothing);
    expect(find.text('Sado forgot it.'), findsOneWidget);
    expect(repository.saved, isEmpty);
  });
}
