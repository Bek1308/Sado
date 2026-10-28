import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/domain/repositories/memory_repository.dart';

final class FakeMemoryRepository implements MemoryRepository {
  FakeMemoryRepository([List<Memory> memories = const []])
    : saved = [...memories];

  final List<Memory> saved;

  /// When set, every call fails with this failure.
  Failure? failure;

  @override
  Future<Result<List<Memory>>> fetchAll() async =>
      failure == null ? Ok([...saved]) : Err(failure!);

  @override
  Future<Result<Memory>> remember(String text) async {
    if (failure case final failure?) return Err(failure);
    final memory = Memory(
      id: 'm${saved.length + 1}',
      text: text,
      createdAt: DateTime(2026, 10, 28),
    );
    saved.insert(0, memory);
    return Ok(memory);
  }

  @override
  Future<Result<void>> forget(String memoryId) async {
    if (failure case final failure?) return Err(failure);
    saved.removeWhere((memory) => memory.id == memoryId);
    return const Ok(null);
  }
}
