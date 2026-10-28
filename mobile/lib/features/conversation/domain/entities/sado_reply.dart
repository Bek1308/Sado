final class SadoReply {
  const SadoReply({
    required this.text,
    this.remembered = const [],
    this.reminded = const [],
  });

  final String text;

  /// Facts Sado saved to its memory while answering.
  final List<String> remembered;

  /// Reminders Sado set while answering.
  final List<String> reminded;
}
