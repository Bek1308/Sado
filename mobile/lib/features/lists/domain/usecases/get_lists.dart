import 'package:sado/core/error/result.dart';
import 'package:sado/features/lists/domain/entities/sado_list.dart';
import 'package:sado/features/lists/domain/repositories/list_repository.dart';

final class GetLists {
  const GetLists(this._repository);

  final ListRepository _repository;

  Future<Result<List<SadoList>>> call() => _repository.fetchAll();
}
