import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/data/datasources/speech_remote_data_source.dart';
import 'package:sado/features/speech/data/repositories/speech_repository_impl.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class _MockRemoteDataSource extends Mock implements SpeechRemoteDataSource {}

void main() {
  late _MockRemoteDataSource remoteDataSource;
  late SpeechRepositoryImpl repository;

  setUpAll(() => registerFallbackValue(SpokenLanguage.english));

  setUp(() {
    remoteDataSource = _MockRemoteDataSource();
    repository = SpeechRepositoryImpl(remoteDataSource);
  });

  Future<Uint8List> synthesize() => remoteDataSource.synthesize(
    text: any(named: 'text'),
    language: any(named: 'language'),
  );

  test('returns the audio bytes from the server', () async {
    final wav = Uint8List.fromList([82, 73, 70, 70]);
    when(synthesize).thenAnswer((_) async => wav);

    final result = await repository.synthesize(
      text: 'salom',
      language: SpokenLanguage.uzbek,
    );

    expect(result, isA<Ok<Uint8List>>().having((ok) => ok.value, 'value', wav));
  });

  test('passes the server explanation through on a rejected request', () async {
    final request = RequestOptions(path: '/speech');
    when(synthesize).thenThrow(
      DioException.badResponse(
        statusCode: 422,
        requestOptions: request,
        response: Response(
          requestOptions: request,
          statusCode: 422,
          data: {'detail': 'Text must contain at least one character'},
        ),
      ),
    );

    final result = await repository.synthesize(
      text: ' ',
      language: SpokenLanguage.uzbek,
    );

    expect(
      result,
      isA<Err<Uint8List>>().having(
        (err) => err.failure,
        'failure',
        isA<ServerFailure>().having(
          (failure) => failure.message,
          'message',
          'Text must contain at least one character',
        ),
      ),
    );
  });
}
