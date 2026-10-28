import 'package:dio/dio.dart';
import 'package:sado/features/memory/data/models/memory_dto.dart';

class MemoryRemoteDataSource {
  const MemoryRemoteDataSource(this._httpClient);

  static const _memoriesPath = '/memories';

  final Dio _httpClient;

  Future<List<MemoryDto>> fetchAll() async {
    final response = await _httpClient.get<List<dynamic>>(_memoriesPath);
    return [
      for (final json in response.data!)
        MemoryDto.fromJson(json as Map<String, dynamic>),
    ];
  }

  Future<MemoryDto> remember(String text) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _memoriesPath,
      data: {'text': text},
    );
    return MemoryDto.fromJson(response.data!);
  }

  Future<void> forget(String memoryId) =>
      _httpClient.delete<void>('$_memoriesPath/$memoryId');
}
