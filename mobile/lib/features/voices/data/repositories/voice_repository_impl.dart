import 'package:dio/dio.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/dio_failure.dart';
import 'package:sado/features/voices/data/datasources/voice_remote_data_source.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';
import 'package:sado/features/voices/domain/repositories/voice_repository.dart';

final class VoiceRepositoryImpl implements VoiceRepository {
  const VoiceRepositoryImpl(this._remoteDataSource);

  final VoiceRemoteDataSource _remoteDataSource;

  @override
  Future<Result<List<VoiceOption>>> fetchVoices() async {
    try {
      final dtos = await _remoteDataSource.fetchVoices();
      return Ok([for (final dto in dtos) dto.toEntity()]);
    } on DioException catch (error) {
      return Err(error.toFailure());
    }
  }
}
