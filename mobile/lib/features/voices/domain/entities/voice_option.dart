final class VoiceOption {
  const VoiceOption({
    required this.id,
    required this.name,
    required this.isDefault,
    this.description = '',
  });

  final String id;
  final String name;
  final String description;
  final bool isDefault;
}
