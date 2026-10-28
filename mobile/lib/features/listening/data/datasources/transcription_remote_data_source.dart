import 'package:dio/dio.dart';
import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class TranscriptionRemoteDataSource {
  const TranscriptionRemoteDataSource(this._httpClient);

  static const _transcriptionsPath = '/transcriptions';

  final Dio _httpClient;

  Future<String> transcribe(
    RecordedAudio recording,
    SpokenLanguage language,
  ) async {
    final form = FormData.fromMap({
      'language': language.code,
      'audio': await MultipartFile.fromFile(
        recording.path,
        contentType: DioMediaType.parse(recording.mimeType),
      ),
    });
    final response = await _httpClient.post<Map<String, dynamic>>(
      _transcriptionsPath,
      data: form,
    );
    return response.data!['text'] as String;
  }
}
