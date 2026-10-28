import 'package:sado/features/memory/domain/entities/memory.dart';

final class MemoryDto {
  const MemoryDto({
    required this.id,
    required this.text,
    required this.createdAt,
  });

  factory MemoryDto.fromJson(Map<String, dynamic> json) => MemoryDto(
    id: json['id'] as String,
    text: json['text'] as String,
    createdAt: DateTime.parse(json['created_at'] as String),
  );

  final String id;
  final String text;
  final DateTime createdAt;

  Memory toEntity() =>
      Memory(id: id, text: text, createdAt: createdAt.toLocal());
}
