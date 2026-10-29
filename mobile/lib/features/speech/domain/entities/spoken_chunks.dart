final _sentenceEnd = RegExp(r'(?<=[.!?…])\s+');

/// Splits a reply into pieces Sado can start speaking one after another.
///
/// The first sentence is voiced while the rest are still being prepared.
/// Very short sentences ride along with the next one, so the voice keeps
/// its rhythm instead of stopping after every "Ha.".
List<String> spokenChunks(String text, {int minLength = 20}) {
  final chunks = <String>[];
  var pending = '';
  for (final sentence in text.trim().split(_sentenceEnd)) {
    if (sentence.isEmpty) continue;
    pending = pending.isEmpty ? sentence : '$pending $sentence';
    if (pending.length >= minLength) {
      chunks.add(pending);
      pending = '';
    }
  }
  if (pending.isNotEmpty) {
    if (chunks.isEmpty) {
      chunks.add(pending);
    } else {
      chunks[chunks.length - 1] = '${chunks.last} $pending';
    }
  }
  return chunks;
}
