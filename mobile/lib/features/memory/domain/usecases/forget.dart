import 'package:sado/core/error/result.dart';
import 'package:sado/features/memory/domain/repositories/memory_repository.dart';

final class Forget {
  const Forget(this._repository);

  final MemoryRepository _repository;

  Future<Result<void>> call(String memoryId) => _repository.forget(memoryId);
}
