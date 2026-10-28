import 'package:dio/dio.dart';
import 'package:sado/core/camera/photo_picker.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class ExplanationRemoteDataSource {
  const ExplanationRemoteDataSource(this._httpClient);

  static const _explanationsPath = '/explanations';

  final Dio _httpClient;

  Future<String> explain(
    Photograph photo,
    SpokenLanguage language,
  ) async {
    final form = FormData.fromMap({
      'language': language.code,
      'file': await MultipartFile.fromFile(
        photo.path,
        contentType: DioMediaType.parse(photo.mimeType),
      ),
    });
    final response = await _httpClient.post<Map<String, dynamic>>(
      _explanationsPath,
      data: form,
    );
    return response.data!['explanation'] as String;
  }
}
