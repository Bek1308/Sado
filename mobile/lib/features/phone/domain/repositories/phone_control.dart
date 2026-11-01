import 'package:sado/features/phone/domain/entities/phone_action.dart';

/// The phone Sado runs on, as far as Sado may act on it.
abstract interface class PhoneControl {
  /// Whether this device can carry out phone actions at all.
  bool get supported;

  Future<PhoneOutcome> perform(PhoneAction action);
}
