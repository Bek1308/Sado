/// The emotional colour of a whole sentence. Codes match the server.
enum Mood {
  neutral(code: 'neutral', label: 'Neutral', emoji: '🙂'),
  happy(code: 'happy', label: 'Happy', emoji: '😄'),
  calm(code: 'calm', label: 'Calm', emoji: '😌'),
  sad(code: 'sad', label: 'Sad', emoji: '😢'),
  excited(code: 'excited', label: 'Excited', emoji: '🤩'),
  serious(code: 'serious', label: 'Serious', emoji: '🧐');

  const Mood({required this.code, required this.label, required this.emoji});

  final String code;
  final String label;
  final String emoji;
}
