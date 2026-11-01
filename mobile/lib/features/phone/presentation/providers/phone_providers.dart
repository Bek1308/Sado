import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/phone/data/android_phone_control.dart';
import 'package:sado/features/phone/domain/repositories/phone_control.dart';

final phoneControlProvider = Provider<PhoneControl>(
  (ref) => !kIsWeb && defaultTargetPlatform == TargetPlatform.android
      ? const AndroidPhoneControl()
      : const NoPhoneControl(),
);
