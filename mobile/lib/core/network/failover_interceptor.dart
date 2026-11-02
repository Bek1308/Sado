import 'package:dio/dio.dart';

/// Keeps Sado answering when its main server is away, e.g. the laptop it runs
/// on is closed: a request the main server cannot take is sent again to the
/// backup, and Sado stays there for a while before trying the main one again.
class FailoverInterceptor extends Interceptor {
  FailoverInterceptor({
    required this.dio,
    required this.primary,
    required this.backup,
    DateTime Function()? now,
    this.stayOnBackup = const Duration(minutes: 2),
  }) : _now = now ?? DateTime.now;

  final Dio dio;
  final String primary;
  final String backup;

  /// How long to keep using the backup before giving the main server
  /// another chance.
  final Duration stayOnBackup;
  final DateTime Function() _now;
  DateTime? _onBackupSince;

  // A tunnel in front of a sleeping laptop answers with a gateway error
  // rather than not answering at all.
  static const _gatewayErrors = {502, 503, 504, 530};
  static const _retriedKey = 'sado.failover.retried';

  bool get _usingBackup {
    final since = _onBackupSince;
    if (since == null) return false;
    if (_now().difference(since) < stayOnBackup) return true;
    _onBackupSince = null;
    return false;
  }

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.baseUrl = _usingBackup ? backup : primary;
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final request = err.requestOptions;
    final onPrimary = request.baseUrl == primary;
    if (!onPrimary ||
        request.extra[_retriedKey] == true ||
        !_unreachable(err)) {
      return handler.next(err);
    }
    _onBackupSince = _now();
    final data = request.data;
    final retry = request.copyWith(
      baseUrl: backup,
      // A form's body is read once; the copy sends it again.
      data: data is FormData ? data.clone() : data,
      extra: {...request.extra, _retriedKey: true},
    );
    try {
      handler.resolve(await dio.fetch<dynamic>(retry));
    } on DioException catch (error) {
      handler.next(error);
    }
  }

  static bool _unreachable(DioException err) => switch (err.type) {
    DioExceptionType.connectionError ||
    DioExceptionType.connectionTimeout => true,
    DioExceptionType.badResponse => _gatewayErrors.contains(
      err.response?.statusCode,
    ),
    _ => false,
  };
}
