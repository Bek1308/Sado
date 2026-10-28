import 'package:sado/core/error/result.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/domain/repositories/memory_repository.dart';

final class Remember {
  const Remember(this._repository);

  final MemoryRepository _repository;

  Future<Result<Memory>> call(String text) => _repository.remember(text);
}
