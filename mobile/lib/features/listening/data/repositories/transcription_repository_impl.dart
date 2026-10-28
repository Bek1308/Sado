import 'package:dio/dio.dart';
import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/dio_failure.dart';
import 'package:sado/features/listening/data/datasources/transcription_remote_data_source.dart';
import 'package:sado/features/listening/domain/entities/transcription.dart';
import 'package:sado/features/listening/domain/repositories/transcription_repository.dart';

final class TranscriptionRepositoryImpl implements TranscriptionRepository {
  const TranscriptionRepositoryImpl(this._remoteDataSource);

  final TranscriptionRemoteDataSource _remoteDataSource;

  @override
  Future<Result<Transcription>> transcribe(RecordedAudio recording) async {
    try {
      return Ok(await _remoteDataSource.transcribe(recording));
    } on DioException catch (error) {
      return Err(error.toFailure());
    }
  }
}
