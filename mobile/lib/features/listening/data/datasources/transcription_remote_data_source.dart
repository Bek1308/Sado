import 'package:dio/dio.dart';
import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/features/listening/domain/entities/transcription.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class TranscriptionRemoteDataSource {
  const TranscriptionRemoteDataSource(this._httpClient);

  static const _transcriptionsPath = '/transcriptions';

  final Dio _httpClient;

  /// Sends audio without a language; the server detects it.
  Future<Transcription> transcribe(RecordedAudio recording) async {
    final form = FormData.fromMap({
      'audio': await MultipartFile.fromFile(
        recording.path,
        contentType: DioMediaType.parse(recording.mimeType),
      ),
    });
    final response = await _httpClient.post<Map<String, dynamic>>(
      _transcriptionsPath,
      data: form,
    );
    final data = response.data!;
    return (
      text: data['text'] as String,
      language: SpokenLanguage.fromCode(data['language'] as String),
    );
  }
}
