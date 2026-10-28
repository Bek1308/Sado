/// A fact the user asked Sado to keep, in the user's own words.
final class Memory {
  const Memory({required this.id, required this.text, required this.createdAt});

  final String id;
  final String text;
  final DateTime createdAt;
}
