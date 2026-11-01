/// Something Sado asked the phone to do, such as opening the dialer for a
/// contact or setting an alarm. The app carries it out with the phone's own
/// screens, so a call or a message still waits for the user's tap.
final class PhoneAction {
  const PhoneAction({required this.kind, required this.details});

  /// What to do: call, message, alarm, timer, open, navigate or flashlight.
  final String kind;
  final Map<String, String> details;

  /// The person, app or place the action is about, to name it to the user.
  String get subject =>
      details['contact'] ?? details['target'] ?? details['destination'] ?? '';
}

/// How carrying out a [PhoneAction] went.
enum PhoneOutcome {
  done,
  contactNotFound,
  appNotFound,
  noPermission,
  failed;

  static PhoneOutcome fromCode(String? code) => switch (code) {
    'done' => done,
    'contact_not_found' => contactNotFound,
    'app_not_found' => appNotFound,
    'no_permission' => noPermission,
    _ => failed,
  };
}
