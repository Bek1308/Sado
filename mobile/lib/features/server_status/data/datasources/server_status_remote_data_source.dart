import 'package:dio/dio.dart';
import 'package:sado/features/server_status/data/models/server_status_dto.dart';

class ServerStatusRemoteDataSource {
  const ServerStatusRemoteDataSource(this._httpClient);

  static const _healthPath = '/health';

  final Dio _httpClient;

  Future<ServerStatusDto> fetchHealth() async {
    final response = await _httpClient.get<Map<String, dynamic>>(_healthPath);
    return ServerStatusDto.fromJson(response.data!);
  }
}
