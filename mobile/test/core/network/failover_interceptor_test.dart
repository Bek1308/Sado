import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/network/failover_interceptor.dart';

const _laptop = 'https://laptop.test';
const _cloud = 'https://cloud.test';

/// Answers like the two servers: the laptop is closed, or open.
final class _Servers implements HttpClientAdapter {
  _Servers({required this.laptopOpen});

  bool laptopOpen;
  final hosts = <String>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    hosts.add(options.uri.host);
    if (options.uri.host == 'laptop.test' && !laptopOpen) {
      return ResponseBody.fromString('Bad gateway', 502);
    }
    return ResponseBody.fromString(
      '{"from":"${options.uri.host}"}',
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

(Dio, _Servers, void Function(Duration)) _client({required bool laptopOpen}) {
  var now = DateTime(2026, 11, 2, 9);
  final servers = _Servers(laptopOpen: laptopOpen);
  final dio = Dio(BaseOptions(baseUrl: _laptop))..httpClientAdapter = servers;
  dio.interceptors.add(
    FailoverInterceptor(
      dio: dio,
      primary: _laptop,
      backup: _cloud,
      now: () => now,
    ),
  );
  return (dio, servers, (wait) => now = now.add(wait));
}

void main() {
  test('uses the laptop while it is open', () async {
    final (dio, servers, _) = _client(laptopOpen: true);

    final response = await dio.get<Map<String, dynamic>>('/health');

    expect(response.data?['from'], 'laptop.test');
    expect(servers.hosts, ['laptop.test']);
  });

  test('turns to the cloud when the laptop is closed', () async {
    final (dio, servers, _) = _client(laptopOpen: false);

    final response = await dio.post<Map<String, dynamic>>(
      '/transcriptions',
      data: FormData.fromMap({'language': 'uz'}),
    );
    await dio.get<void>('/health');

    expect(response.data?['from'], 'cloud.test');
    expect(servers.hosts, ['laptop.test', 'cloud.test', 'cloud.test']);
  });

  test('goes back to the laptop after a while', () async {
    final (dio, servers, wait) = _client(laptopOpen: false);
    await dio.get<void>('/health');
    servers.laptopOpen = true;

    wait(const Duration(minutes: 3));
    final response = await dio.get<Map<String, dynamic>>('/health');

    expect(response.data?['from'], 'laptop.test');
  });
}
