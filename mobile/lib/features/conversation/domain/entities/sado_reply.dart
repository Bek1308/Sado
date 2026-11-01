import 'package:sado/features/conversation/domain/entities/pending_action.dart';
import 'package:sado/features/phone/domain/entities/phone_action.dart';

final class SadoReply {
  const SadoReply({
    required this.text,
    this.remembered = const [],
    this.reminded = const [],
    this.listsChanged = false,
    this.pendingAction,
    this.phoneActions = const [],
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

  /// What the phone should do now, e.g. open the dialer for a contact.
  final List<PhoneAction> phoneActions;

  /// The same reply with Sado's words replaced, e.g. when the phone could not
  /// do what Sado said it would.
  SadoReply saying(String text) => SadoReply(
    text: text,
    remembered: remembered,
    reminded: reminded,
    listsChanged: listsChanged,
    pendingAction: pendingAction,
  );
}
