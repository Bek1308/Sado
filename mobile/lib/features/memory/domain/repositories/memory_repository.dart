import 'package:sado/core/error/result.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';

abstract interface class MemoryRepository {
  /// Newest first.
  Future<Result<List<Memory>>> fetchAll();

  Future<Result<Memory>> remember(String text);

  Future<Result<void>> forget(String memoryId);
}
