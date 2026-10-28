import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/memory/data/datasources/memory_remote_data_source.dart';
import 'package:sado/features/memory/data/repositories/memory_repository_impl.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/domain/repositories/memory_repository.dart';
import 'package:sado/features/memory/domain/usecases/forget.dart';
import 'package:sado/features/memory/domain/usecases/get_memories.dart';
import 'package:sado/features/memory/domain/usecases/remember.dart';

final memoryRepositoryProvider = Provider<MemoryRepository>(
  (ref) => MemoryRepositoryImpl(
    MemoryRemoteDataSource(ref.watch(httpClientProvider)),
  ),
);

final memoriesControllerProvider =
    AsyncNotifierProvider<MemoriesController, List<Memory>>(
      MemoriesController.new,
    );

class MemoriesController extends AsyncNotifier<List<Memory>> {
  MemoryRepository get _repository => ref.read(memoryRepositoryProvider);

  @override
  Future<List<Memory>> build() async {
    final result = await GetMemories(_repository).call();
    return switch (result) {
      Ok(:final value) => value,
      Err(:final failure) => throw failure,
    };
  }

  /// Returns why Sado could not remember [text], or `null` on success.
  Future<String?> remember(String text) async {
    final result = await Remember(_repository).call(text);
    switch (result) {
      case Ok(:final value):
        state = AsyncData([value, ...?state.value]);
        return null;
      case Err(:final failure):
        return failure.message;
    }
  }

  /// Removes [memory] at once and puts it back if the server refuses.
  /// Returns why it could not be forgotten, or `null` on success.
  Future<String?> forget(Memory memory) async {
    final before = state.value ?? const <Memory>[];
    state = AsyncData([
      for (final kept in before)
        if (kept.id != memory.id) kept,
    ]);

    final result = await Forget(_repository).call(memory.id);
    if (result case Err(:final failure)) {
      state = AsyncData(before);
      return failure.message;
    }
    return null;
  }
}
