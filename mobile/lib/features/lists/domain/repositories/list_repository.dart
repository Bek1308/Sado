import 'package:sado/core/error/result.dart';
import 'package:sado/features/lists/domain/entities/sado_list.dart';

abstract interface class ListRepository {
  Future<Result<List<SadoList>>> fetchAll();

  Future<Result<void>> removeEntry(String entryId);
}
