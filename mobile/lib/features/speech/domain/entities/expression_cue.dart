/// Emotional cues the server performs when written inline.
///
/// Example: "Voy! [surprise] Rostdanmi?"
enum ExpressionCue {
  laugh(tag: '[laugh]', label: 'Laugh', emoji: '😄'),
  sigh(tag: '[sigh]', label: 'Sigh', emoji: '😮‍💨'),
  surprise(tag: '[surprise]', label: 'Surprise', emoji: '😮'),
  question(tag: '[question]', label: 'Question', emoji: '🤔'),
  hmm(tag: '[hmm]', label: 'Hmm', emoji: '😒');

  const ExpressionCue({
    required this.tag,
    required this.label,
    required this.emoji,
  });

  final String tag;
  final String label;
  final String emoji;

  static final _anyTag = RegExp(
    values.map((cue) => RegExp.escape(cue.tag)).join('|'),
  );
  static final _extraSpaces = RegExp(r'\s{2,}');
  static final _spaceBeforePunctuation = RegExp(r'\s+([.,!?;:])');

  /// The text a person should read: cues are performed, not shown.
  static String withoutCues(String text) => text
      .replaceAll(_anyTag, ' ')
      .replaceAll(_extraSpaces, ' ')
      .replaceAllMapped(_spaceBeforePunctuation, (match) => match[1]!)
      .trim();
}
