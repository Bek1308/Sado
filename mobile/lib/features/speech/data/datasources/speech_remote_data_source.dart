import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class SpeechRemoteDataSource {
  const SpeechRemoteDataSource(this._httpClient);

  static const _speechPath = '/speech';

  final Dio _httpClient;

  Future<Uint8List> synthesize({
    required String text,
    required SpokenLanguage language,
    String? voiceId,
  }) async {
    final response = await _httpClient.post<List<int>>(
      _speechPath,
      data: {
        'text': text,
        'language': language.code,
        'voice': ?voiceId,
      },
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(response.data!);
  }
}
