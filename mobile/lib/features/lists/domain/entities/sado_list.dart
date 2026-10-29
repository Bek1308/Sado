final class ListEntry {
  const ListEntry({required this.id, required this.text});

  final String id;
  final String text;
}

/// One of the lists Sado keeps for the user, e.g. shopping or to-do.
final class SadoList {
  const SadoList({required this.name, required this.entries});

  final String name;
  final List<ListEntry> entries;
}
