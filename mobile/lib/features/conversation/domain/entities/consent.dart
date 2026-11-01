enum Consent { yes, no, unclear }

final _apostrophes = RegExp('[‘’ʻ`´]');
final _punctuation = RegExp(r"[^\p{L}\p{N}\s']", unicode: true);
final _spaces = RegExp(r'\s+');

/// Short answers in Sado's four languages, so a confirmation can be spoken.
const _yes = {
  'ha', 'xa', "xo'p", 'mayli', 'albatta', "bo'pti", 'qil', //
  'ҳа', 'бале', 'хуб', 'майлӣ', 'албатта',
  'да', 'давай', 'конечно', 'хорошо', 'ок', 'ага',
  'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'go ahead', 'do it',
};
const _no = {
  "yo'q", 'yoq', 'kerak emas', 'bekor qil', "to'xta", //
  'не', 'нет', 'не надо', 'отмена', 'стоп', 'не лозим', 'бекор кун',
  'no', 'nope', 'cancel', 'stop', "don't",
};

/// Reads whether a short spoken reply agrees. Anything longer than a few
/// words is a new request rather than an answer.
Consent consentIn(String text) {
  final words = text
      .toLowerCase()
      .replaceAll(_apostrophes, "'")
      .replaceAll(_punctuation, ' ')
      .split(_spaces)
      .where((word) => word.isNotEmpty)
      .toList();
  if (words.isEmpty || words.length > 4) return Consent.unclear;
  final phrase = words.join(' ');
  bool says(Set<String> answers) =>
      answers.contains(words.first) ||
      answers.any(
        (answer) => phrase == answer || phrase.startsWith('$answer '),
      );
  // "Yo'q" must win over a "ha" later in the same reply.
  if (says(_no)) return Consent.no;
  if (says(_yes)) return Consent.yes;
  return Consent.unclear;
}
