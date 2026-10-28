import 'package:sado/features/voices/domain/entities/voice_option.dart';

final class VoiceOptionDto {
  const VoiceOptionDto({
    required this.id,
    required this.name,
    required this.description,
    required this.isDefault,
  });

  factory VoiceOptionDto.fromJson(Map<String, dynamic> json) => VoiceOptionDto(
    id: json['id'] as String,
    name: json['name'] as String,
    // Older servers did not describe their voices.
    description: json['description'] as String? ?? '',
    isDefault: json['is_default'] as bool,
  );

  final String id;
  final String name;
  final String description;
  final bool isDefault;

  VoiceOption toEntity() => VoiceOption(
    id: id,
    name: name,
    description: description,
    isDefault: isDefault,
  );
}
