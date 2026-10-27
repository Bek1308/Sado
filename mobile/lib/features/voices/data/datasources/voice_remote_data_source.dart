import 'package:dio/dio.dart';
import 'package:sado/features/voices/data/models/voice_option_dto.dart';

class VoiceRemoteDataSource {
  const VoiceRemoteDataSource(this._httpClient);

  static const _voicesPath = '/voices';

  final Dio _httpClient;

  Future<List<VoiceOptionDto>> fetchVoices() async {
    final response = await _httpClient.get<List<dynamic>>(_voicesPath);
    return [
      for (final json in response.data!)
        VoiceOptionDto.fromJson(json as Map<String, dynamic>),
    ];
  }
}
