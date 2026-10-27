import 'package:sado/core/error/result.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';

abstract interface class ServerStatusRepository {
  Future<Result<ServerStatus>> fetchStatus();
}
