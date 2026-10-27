import 'package:dio/dio.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/server_status/data/datasources/server_status_remote_data_source.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';
import 'package:sado/features/server_status/domain/repositories/server_status_repository.dart';

final class ServerStatusRepositoryImpl implements ServerStatusRepository {
  const ServerStatusRepositoryImpl(this._remoteDataSource);

  final ServerStatusRemoteDataSource _remoteDataSource;

  @override
  Future<Result<ServerStatus>> fetchStatus() async {
    try {
      final dto = await _remoteDataSource.fetchHealth();
      return Ok(dto.toEntity());
    } on DioException catch (error) {
      return Err(_toFailure(error));
    }
  }

  Failure _toFailure(DioException error) => switch (error.type) {
    DioExceptionType.badResponse => ServerFailure(
      'Server responded with ${error.response?.statusCode}',
    ),
    _ => const NetworkFailure('Server is unreachable'),
  };
}
