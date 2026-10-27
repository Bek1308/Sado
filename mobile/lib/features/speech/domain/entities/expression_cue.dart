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
}
