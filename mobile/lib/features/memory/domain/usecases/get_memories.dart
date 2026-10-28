import 'package:sado/core/error/result.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/domain/repositories/memory_repository.dart';

final class GetMemories {
  const GetMemories(this._repository);

  final MemoryRepository _repository;

  Future<Result<List<Memory>>> call() => _repository.fetchAll();
}
