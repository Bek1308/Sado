import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/config/app_config.dart';
import 'package:sado/core/network/failover_interceptor.dart';

final httpClientProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: AppConfig.connectTimeout,
      receiveTimeout: AppConfig.receiveTimeout,
      headers: {
        if (AppConfig.desktopToken.isNotEmpty)
          'X-Sado-Desktop-Token': AppConfig.desktopToken,
      },
    ),
  );
  if (AppConfig.backupApiBaseUrl.isNotEmpty) {
    dio.interceptors.add(
      FailoverInterceptor(
        dio: dio,
        primary: AppConfig.apiBaseUrl,
        backup: AppConfig.backupApiBaseUrl,
      ),
    );
  }
  return dio;
});
