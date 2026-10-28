import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sado/core/audio/voice_recorder.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/listening/data/datasources/transcription_remote_data_source.dart';
import 'package:sado/features/listening/data/repositories/transcription_repository_impl.dart';
import 'package:sado/features/listening/domain/entities/transcription.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class _MockRemoteDataSource extends Mock
    implements TranscriptionRemoteDataSource {}

const _recording = RecordedAudio(path: '/tmp/a.m4a', mimeType: 'audio/mp4');

void main() {
  late _MockRemoteDataSource remoteDataSource;
  late TranscriptionRepositoryImpl repository;

  setUp(() {
    remoteDataSource = _MockRemoteDataSource();
    repository = TranscriptionRepositoryImpl(remoteDataSource);
  });

  test('returns the transcript from the server', () async {
    when(
      () => remoteDataSource.transcribe(_recording),
    ).thenAnswer(
      (_) async => (text: 'salom', language: SpokenLanguage.uzbek),
    );

    final result = await repository.transcribe(_recording);

    expect(
      result,
      isA<Ok<Transcription>>().having(
        (ok) => ok.value,
        'value',
        (text: 'salom', language: SpokenLanguage.uzbek),
      ),
    );
  });

  test('explains when speech recognition is unavailable', () async {
    final request = RequestOptions(path: '/transcriptions');
    when(
      () => remoteDataSource.transcribe(_recording),
    ).thenThrow(
      DioException.badResponse(
        statusCode: 503,
        requestOptions: request,
        response: Response(
          requestOptions: request,
          statusCode: 503,
          data: {'detail': 'Speech recognition is temporarily unavailable'},
        ),
      ),
    );

    final result = await repository.transcribe(_recording);

    expect(
      result,
      isA<Err<Transcription>>().having(
        (err) => err.failure,
        'failure',
        isA<ServerFailure>().having(
          (failure) => failure.message,
          'message',
          'Speech recognition is temporarily unavailable',
        ),
      ),
    );
  });
}
