import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/server_status/data/datasources/server_status_remote_data_source.dart';
import 'package:sado/features/server_status/data/models/server_status_dto.dart';
import 'package:sado/features/server_status/data/repositories/server_status_repository_impl.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';

class _MockRemoteDataSource extends Mock
    implements ServerStatusRemoteDataSource {}

void main() {
  late _MockRemoteDataSource remoteDataSource;
  late ServerStatusRepositoryImpl repository;

  setUp(() {
    remoteDataSource = _MockRemoteDataSource();
    repository = ServerStatusRepositoryImpl(remoteDataSource);
  });

  test('returns the server status when the server answers', () async {
    when(remoteDataSource.fetchHealth).thenAnswer(
      (_) async => const ServerStatusDto(name: 'Sado', version: '0.1.0'),
    );

    final result = await repository.fetchStatus();

    expect(
      result,
      isA<Ok<ServerStatus>>()
          .having((ok) => ok.value.name, 'name', 'Sado')
          .having((ok) => ok.value.version, 'version', '0.1.0'),
    );
  });

  test('returns a network failure when the server is unreachable', () async {
    when(remoteDataSource.fetchHealth).thenThrow(
      DioException.connectionError(
        requestOptions: RequestOptions(),
        reason: 'refused',
      ),
    );

    final result = await repository.fetchStatus();

    expect(
      result,
      isA<Err<ServerStatus>>().having(
        (err) => err.failure,
        'failure',
        isA<NetworkFailure>(),
      ),
    );
  });
}
