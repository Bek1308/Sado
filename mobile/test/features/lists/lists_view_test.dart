import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/lists/domain/entities/sado_list.dart';
import 'package:sado/features/lists/domain/repositories/list_repository.dart';
import 'package:sado/features/lists/presentation/providers/list_providers.dart';
import 'package:sado/features/lists/presentation/widgets/lists_view.dart';

final class _FakeLists implements ListRepository {
  _FakeLists(this.lists);

  List<SadoList> lists;
  Failure? failure;

  @override
  Future<Result<List<SadoList>>> fetchAll() async => Ok(lists);

  @override
  Future<Result<void>> removeEntry(String entryId) async {
    if (failure case final failure?) return Err(failure);
    return const Ok(null);
  }
}

const _shopping = SadoList(
  name: 'xarid',
  entries: [
    ListEntry(id: 'a', text: 'non'),
    ListEntry(id: 'b', text: 'olma'),
  ],
);

Future<void> _pump(WidgetTester tester, _FakeLists repository) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [listRepositoryProvider.overrideWithValue(repository)],
      child: const MaterialApp(home: Scaffold(body: ListsView())),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows each list with its entries', (tester) async {
    await _pump(tester, _FakeLists([_shopping]));

    expect(find.text('Xarid'), findsOneWidget);
    expect(find.text('non'), findsOneWidget);
    expect(find.text('olma'), findsOneWidget);
  });

  testWidgets('explains how to start a list when there are none', (
    tester,
  ) async {
    await _pump(tester, _FakeLists([]));

    expect(find.text('No lists yet'), findsOneWidget);
  });

  testWidgets('ticking an entry crosses it off', (tester) async {
    await _pump(tester, _FakeLists([_shopping]));

    await tester.tap(find.text('non'));
    await tester.pumpAndSettle();

    expect(find.text('non'), findsNothing);
    expect(find.text('olma'), findsOneWidget);
  });

  testWidgets('an entry comes back when the server refuses', (tester) async {
    final repository = _FakeLists([_shopping])
      ..failure = const NetworkFailure('Offline');
    await _pump(tester, repository);

    await tester.tap(find.text('non'));
    await tester.pumpAndSettle();

    expect(find.text('non'), findsOneWidget);
    expect(find.text('Offline'), findsOneWidget);
  });
}
