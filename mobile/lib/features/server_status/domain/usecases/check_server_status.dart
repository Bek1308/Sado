import 'package:sado/core/error/result.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';
import 'package:sado/features/server_status/domain/repositories/server_status_repository.dart';

final class CheckServerStatus {
  const CheckServerStatus(this._repository);

  final ServerStatusRepository _repository;

  Future<Result<ServerStatus>> call() => _repository.fetchStatus();
}
