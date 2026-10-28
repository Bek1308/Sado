import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/network/dio_failure.dart';

final _request = RequestOptions(path: '/replies');

DioException _response(int statusCode, Object? data) => DioException(
  requestOptions: _request,
  type: DioExceptionType.badResponse,
  response: Response<Object?>(
    requestOptions: _request,
    statusCode: statusCode,
    data: data,
  ),
);

void main() {
  test("shows Sado's own explanation", () {
    final failure = _response(503, {
      'detail': 'Sado cannot think right now; please try again',
    }).toFailure();

    expect(failure, isA<ServerFailure>());
    expect(failure.message, 'Sado cannot think right now; please try again');
  });

  test('explains a missing server instead of showing a status code', () {
    final failure = _response(404, 'Tunnel not found').toFailure();

    expect(
      failure.message,
      'Sado is offline right now. Please try again in a moment.',
    );
  });

  test('tells the user to check the connection when nothing answers', () {
    final failure = DioException(
      requestOptions: _request,
      type: DioExceptionType.connectionError,
    ).toFailure();

    expect(failure, isA<NetworkFailure>());
    expect(
      failure.message,
      "Can't reach Sado. Check your internet connection.",
    );
  });

  test('says when Sado is too slow', () {
    final failure = DioException(
      requestOptions: _request,
      type: DioExceptionType.receiveTimeout,
    ).toFailure();

    expect(failure.message, 'Sado is taking too long. Please try again.');
  });
}
