import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/presentation/providers/memory_providers.dart';

import 'fake_memory_repository.dart';

final _name = Memory(
  id: 'name',
  text: 'Ismim Aziz',
  createdAt: DateTime(2026, 10, 27),
);

ProviderContainer _container(FakeMemoryRepository repository) {
  final container = ProviderContainer(
    overrides: [memoryRepositoryProvider.overrideWithValue(repository)],
  );
  addTearDown(container.dispose);
  return container;
}

void main() {
  test('adds a new memory to the top of the list', () async {
    final container = _container(FakeMemoryRepository([_name]));
    await container.read(memoriesControllerProvider.future);

    final problem = await container
        .read(memoriesControllerProvider.notifier)
        .remember('Choyni yaxshi ko‘raman');

    expect(problem, isNull);
    expect(
      container.read(memoriesControllerProvider).value!.map((m) => m.text),
      ['Choyni yaxshi ko‘raman', 'Ismim Aziz'],
    );
  });

  test('puts a memory back when the server refuses to forget it', () async {
    final repository = FakeMemoryRepository([_name]);
    final container = _container(repository);
    await container.read(memoriesControllerProvider.future);
    repository.failure = const NetworkFailure('Offline');

    final problem = await container
        .read(memoriesControllerProvider.notifier)
        .forget(_name);

    expect(problem, 'Offline');
    expect(container.read(memoriesControllerProvider).value, [_name]);
  });

  test('forgets a memory', () async {
    final repository = FakeMemoryRepository([_name]);
    final container = _container(repository);
    await container.read(memoriesControllerProvider.future);

    await container.read(memoriesControllerProvider.notifier).forget(_name);

    expect(container.read(memoriesControllerProvider).value, isEmpty);
    expect(repository.saved, isEmpty);
  });
}
