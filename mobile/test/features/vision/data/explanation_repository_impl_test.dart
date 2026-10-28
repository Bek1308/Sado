import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sado/core/camera/photo_picker.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/vision/data/datasources/explanation_remote_data_source.dart';
import 'package:sado/features/vision/data/repositories/explanation_repository_impl.dart';

class _MockRemoteDataSource extends Mock
    implements ExplanationRemoteDataSource {}

const _photo = Photograph(path: '/tmp/notice.jpg', mimeType: 'image/jpeg');

void main() {
  late _MockRemoteDataSource remoteDataSource;
  late ExplanationRepositoryImpl repository;

  setUp(() {
    remoteDataSource = _MockRemoteDataSource();
    repository = ExplanationRepositoryImpl(remoteDataSource);
  });

  test('returns the explanation from the server', () async {
    when(
      () => remoteDataSource.explain(_photo, SpokenLanguage.tajik),
    ).thenAnswer((_) async => 'This is a notice.');

    final result = await repository.explain(_photo, SpokenLanguage.tajik);

    expect(
      result,
      isA<Ok<String>>().having(
        (ok) => ok.value,
        'value',
        'This is a notice.',
      ),
    );
  });

  test('explains when Sado cannot think', () async {
    final request = RequestOptions(path: '/explanations');
    when(
      () => remoteDataSource.explain(_photo, SpokenLanguage.tajik),
    ).thenThrow(
      DioException.badResponse(
        statusCode: 503,
        requestOptions: request,
        response: Response(
          requestOptions: request,
          statusCode: 503,
          data: {'detail': 'Sado cannot think right now; please try again'},
        ),
      ),
    );

    final result = await repository.explain(_photo, SpokenLanguage.tajik);

    expect(
      result,
      isA<Err<String>>().having(
        (err) => err.failure,
        'failure',
        isA<ServerFailure>().having(
          (failure) => failure.message,
          'message',
          'Sado cannot think right now; please try again',
        ),
      ),
    );
  });
}
