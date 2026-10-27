import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/server_status/data/datasources/server_status_remote_data_source.dart';
import 'package:sado/features/server_status/data/repositories/server_status_repository_impl.dart';
import 'package:sado/features/server_status/domain/entities/server_status.dart';
import 'package:sado/features/server_status/domain/repositories/server_status_repository.dart';
import 'package:sado/features/server_status/domain/usecases/check_server_status.dart';

final serverStatusRepositoryProvider = Provider<ServerStatusRepository>(
  (ref) => ServerStatusRepositoryImpl(
    ServerStatusRemoteDataSource(ref.watch(httpClientProvider)),
  ),
);

final checkServerStatusProvider = Provider<CheckServerStatus>(
  (ref) => CheckServerStatus(ref.watch(serverStatusRepositoryProvider)),
);

final serverStatusProvider = FutureProvider<Result<ServerStatus>>(
  (ref) => ref.watch(checkServerStatusProvider).call(),
);
