import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/dio_failure.dart';
import 'package:sado/features/speech/data/datasources/speech_remote_data_source.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/domain/repositories/speech_repository.dart';

final class SpeechRepositoryImpl implements SpeechRepository {
  const SpeechRepositoryImpl(this._remoteDataSource);

  final SpeechRemoteDataSource _remoteDataSource;

  @override
  Future<Result<Uint8List>> synthesize({
    required String text,
    required SpokenLanguage language,
    String? voiceId,
    Mood mood = Mood.neutral,
  }) async {
    try {
      return Ok(
        await _remoteDataSource.synthesize(
          text: text,
          language: language,
          voiceId: voiceId,
          mood: mood,
        ),
      );
    } on DioException catch (error) {
      return Err(error.toFailure());
    }
  }
}
