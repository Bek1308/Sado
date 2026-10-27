import 'package:dio/dio.dart';
import 'package:sado/core/error/failure.dart';

extension DioFailure on DioException {
  Failure toFailure() => switch (type) {
    DioExceptionType.badResponse => ServerFailure(_serverMessage()),
    _ => const NetworkFailure('Server is unreachable'),
  };

  String _serverMessage() {
    final data = response?.data;
    return switch (data) {
      {'detail': final String detail} => detail,
      _ => 'Server responded with ${response?.statusCode}',
    };
  }
}
