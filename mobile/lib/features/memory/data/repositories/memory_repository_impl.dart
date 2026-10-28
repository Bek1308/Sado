import 'package:dio/dio.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/dio_failure.dart';
import 'package:sado/features/memory/data/datasources/memory_remote_data_source.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/domain/repositories/memory_repository.dart';

final class MemoryRepositoryImpl implements MemoryRepository {
  const MemoryRepositoryImpl(this._remoteDataSource);

  final MemoryRemoteDataSource _remoteDataSource;

  @override
  Future<Result<List<Memory>>> fetchAll() => _guard(() async {
    final dtos = await _remoteDataSource.fetchAll();
    return [for (final dto in dtos) dto.toEntity()];
  });

  @override
  Future<Result<Memory>> remember(String text) => _guard(() async {
    final dto = await _remoteDataSource.remember(text);
    return dto.toEntity();
  });

  @override
  Future<Result<void>> forget(String memoryId) =>
      _guard(() => _remoteDataSource.forget(memoryId));

  Future<Result<T>> _guard<T>(Future<T> Function() request) async {
    try {
      return Ok(await request());
    } on DioException catch (error) {
      return Err(error.toFailure());
    }
  }
}
