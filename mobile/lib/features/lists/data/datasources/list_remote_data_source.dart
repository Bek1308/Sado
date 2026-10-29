import 'package:dio/dio.dart';
import 'package:sado/features/lists/data/models/sado_list_dto.dart';

class ListRemoteDataSource {
  const ListRemoteDataSource(this._httpClient);

  static const _listsPath = '/lists';

  final Dio _httpClient;

  Future<List<SadoListDto>> fetchAll() async {
    final response = await _httpClient.get<List<dynamic>>(_listsPath);
    return [
      for (final json in response.data!)
        SadoListDto.fromJson(json as Map<String, dynamic>),
    ];
  }

  Future<void> removeEntry(String entryId) =>
      _httpClient.delete<void>('$_listsPath/items/$entryId');
}
