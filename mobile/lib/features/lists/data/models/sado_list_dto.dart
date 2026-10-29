import 'package:sado/features/lists/domain/entities/sado_list.dart';

final class SadoListDto {
  const SadoListDto({required this.name, required this.entries});

  factory SadoListDto.fromJson(Map<String, dynamic> json) => SadoListDto(
    name: json['name'] as String,
    entries: [
      for (final item in json['items'] as List<dynamic>)
        ListEntry(
          id: (item as Map<String, dynamic>)['id'] as String,
          text: item['text'] as String,
        ),
    ],
  );

  final String name;
  final List<ListEntry> entries;

  SadoList toEntity() => SadoList(name: name, entries: entries);
}
