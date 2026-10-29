import 'package:sado/core/error/result.dart';
import 'package:sado/features/lists/domain/repositories/list_repository.dart';

final class CrossOff {
  const CrossOff(this._repository);

  final ListRepository _repository;

  Future<Result<void>> call(String entryId) => _repository.removeEntry(entryId);
}
