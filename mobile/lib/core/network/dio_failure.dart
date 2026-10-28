import 'package:dio/dio.dart';
import 'package:sado/core/error/failure.dart';

extension DioFailure on DioException {
  Failure toFailure() => switch (type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.sendTimeout ||
    DioExceptionType.receiveTimeout => const NetworkFailure(
      'Sado is taking too long. Please try again.',
    ),
    DioExceptionType.badResponse => ServerFailure(_serverMessage()),
    _ => const NetworkFailure(
      "Can't reach Sado. Check your internet connection.",
    ),
  };

  String _serverMessage() {
    final response = this.response;
    return switch ((response?.statusCode, response?.data)) {
      // Sado explains its own errors; anything else came from a proxy or
      // tunnel in front of it and only means the server is not there.
      (_, {'detail': final String detail}) => detail,
      (404 || 502 || 503 || 504, _) =>
        'Sado is offline right now. Please try again in a moment.',
      _ => 'Something went wrong on Sado’s side. Please try again.',
    };
  }
}
