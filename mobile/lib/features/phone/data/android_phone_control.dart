import 'package:flutter/services.dart';
import 'package:sado/features/phone/domain/entities/phone_action.dart';
import 'package:sado/features/phone/domain/repositories/phone_control.dart';

/// Talks to `PhoneControl.kt`, which uses Android's own dialer, composer,
/// clock and maps.
final class AndroidPhoneControl implements PhoneControl {
  const AndroidPhoneControl();

  static const _channel = MethodChannel('sado/phone');

  @override
  bool get supported => true;

  @override
  Future<PhoneOutcome> perform(PhoneAction action) async {
    try {
      final outcome = await _channel.invokeMethod<String>('perform', {
        'kind': action.kind,
        'details': action.details,
      });
      return PhoneOutcome.fromCode(outcome);
    } on PlatformException {
      return PhoneOutcome.failed;
    }
  }

  @override
  Future<String> status() async {
    try {
      return await _channel.invokeMethod<String>('status') ?? '';
    } on PlatformException {
      return '';
    }
  }
}

/// A computer, or anything else that is not a phone Sado can act on.
final class NoPhoneControl implements PhoneControl {
  const NoPhoneControl();

  @override
  bool get supported => false;

  @override
  Future<PhoneOutcome> perform(PhoneAction action) async => PhoneOutcome.failed;

  @override
  Future<String> status() async => '';
}
