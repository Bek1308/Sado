import 'package:dio/dio.dart';
import 'package:sado/core/camera/photo_picker.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/dio_failure.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/vision/data/datasources/explanation_remote_data_source.dart';
import 'package:sado/features/vision/domain/repositories/explanation_repository.dart';

final class ExplanationRepositoryImpl implements ExplanationRepository {
  const ExplanationRepositoryImpl(this._remoteDataSource);

  final ExplanationRemoteDataSource _remoteDataSource;

  @override
  Future<Result<String>> explain(
    Photograph photo,
    SpokenLanguage language,
  ) async {
    try {
      return Ok(await _remoteDataSource.explain(photo, language));
    } on DioException catch (error) {
      return Err(error.toFailure());
    }
  }
}
