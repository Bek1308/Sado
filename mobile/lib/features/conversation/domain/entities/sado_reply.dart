import 'package:sado/features/conversation/domain/entities/pending_action.dart';

final class SadoReply {
  const SadoReply({
    required this.text,
    this.remembered = const [],
    this.reminded = const [],
    this.listsChanged = false,
    this.pendingAction,
  });

  final String text;

  /// Facts Sado saved to its memory while answering.
  final List<String> remembered;

  /// Reminders Sado set while answering.
  final List<String> reminded;

  /// Whether Sado added to or crossed off one of the user's lists.
  final bool listsChanged;

  /// An action on the user's computer that waits for their yes.
  final PendingAction? pendingAction;
}
