import 'package:dio/dio.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/dio_failure.dart';
import 'package:sado/features/lists/data/datasources/list_remote_data_source.dart';
import 'package:sado/features/lists/domain/entities/sado_list.dart';
import 'package:sado/features/lists/domain/repositories/list_repository.dart';

final class ListRepositoryImpl implements ListRepository {
  const ListRepositoryImpl(this._remoteDataSource);

  final ListRemoteDataSource _remoteDataSource;

  @override
  Future<Result<List<SadoList>>> fetchAll() => _guard(() async {
    final dtos = await _remoteDataSource.fetchAll();
    return [for (final dto in dtos) dto.toEntity()];
  });

  @override
  Future<Result<void>> removeEntry(String entryId) =>
      _guard(() => _remoteDataSource.removeEntry(entryId));

  Future<Result<T>> _guard<T>(Future<T> Function() request) async {
    try {
      return Ok(await request());
    } on DioException catch (error) {
      return Err(error.toFailure());
    }
  }
}
