import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/config/app_config.dart';
import 'package:sado/core/network/failover_interceptor.dart';
import 'package:sado/features/account/presentation/providers/account_providers.dart';

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
  final accounts = ref.watch(accountServiceProvider);
  if (accounts.supported) {
    dio.interceptors.add(
      // Tells the server whose phone is asking, so it opens their own memory.
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await accounts.idToken();
          if (token != null) options.headers['Authorization'] = 'Bearer $token';
          handler.next(options);
        },
      ),
    );
  }
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
