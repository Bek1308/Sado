final class SadoReply {
  const SadoReply({required this.text, this.remembered = const []});

  final String text;

  /// Facts Sado saved to its memory while answering.
  final List<String> remembered;
}
