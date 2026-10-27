import 'package:sado/features/server_status/domain/entities/server_status.dart';

final class ServerStatusDto {
  const ServerStatusDto({required this.name, required this.version});

  factory ServerStatusDto.fromJson(Map<String, dynamic> json) =>
      ServerStatusDto(
        name: json['name'] as String,
        version: json['version'] as String,
      );

  final String name;
  final String version;

  ServerStatus toEntity() => ServerStatus(name: name, version: version);
}
