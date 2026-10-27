import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/voices/data/datasources/voice_remote_data_source.dart';
import 'package:sado/features/voices/data/models/voice_option_dto.dart';
import 'package:sado/features/voices/data/repositories/voice_repository_impl.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';

class _MockRemoteDataSource extends Mock implements VoiceRemoteDataSource {}

void main() {
  late _MockRemoteDataSource remoteDataSource;
  late VoiceRepositoryImpl repository;

  setUp(() {
    remoteDataSource = _MockRemoteDataSource();
    repository = VoiceRepositoryImpl(remoteDataSource);
  });

  test('maps the server voices to domain voices', () async {
    when(remoteDataSource.fetchVoices).thenAnswer(
      (_) async => [
        VoiceOptionDto.fromJson(const {
          'id': 'sado',
          'name': 'Sado',
          'is_default': true,
        }),
        VoiceOptionDto.fromJson(const {
          'id': 'opa',
          'name': 'Opa',
          'is_default': false,
        }),
      ],
    );

    final result = await repository.fetchVoices();

    expect(
      result,
      isA<Ok<List<VoiceOption>>>().having(
        (ok) => [for (final voice in ok.value) (voice.id, voice.isDefault)],
        'voices',
        [('sado', true), ('opa', false)],
      ),
    );
  });

  test('returns a network failure when the server is unreachable', () async {
    when(remoteDataSource.fetchVoices).thenThrow(
      DioException.connectionError(
        requestOptions: RequestOptions(),
        reason: 'refused',
      ),
    );

    final result = await repository.fetchVoices();

    expect(
      result,
      isA<Err<List<VoiceOption>>>().having(
        (err) => err.failure,
        'failure',
        isA<NetworkFailure>(),
      ),
    );
  });
}
