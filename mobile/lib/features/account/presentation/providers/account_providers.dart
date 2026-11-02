import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/config/app_config.dart';
import 'package:sado/core/storage/preferences.dart';
import 'package:sado/features/account/data/firebase_account_service.dart';
import 'package:sado/features/account/domain/account.dart';

/// Sign-in runs on Android, where Firebase is set up in `main`. Widget tests
/// pretend to be Android but run on the developer's machine, without it.
bool get accountsSupported => !kIsWeb && Platform.isAndroid;

final accountServiceProvider = Provider<AccountService>(
  (ref) => accountsSupported
      ? FirebaseAccountService(serverClientId: AppConfig.googleWebClientId)
      : const NoAccountService(),
);

final accountProvider = StreamProvider<Account?>((ref) {
  final service = ref.watch(accountServiceProvider);
  return service.changes;
});

final accountSkippedProvider = NotifierProvider<AccountSkipped, bool>(
  AccountSkipped.new,
);

/// Whether the user chose to try Sado without signing in.
class AccountSkipped extends Notifier<bool> {
  static const _key = 'account_skipped';

  @override
  bool build() => ref.watch(sharedPreferencesProvider).getBool(_key) ?? false;

  Future<void> skip({bool skipped = true}) async {
    state = skipped;
    await ref.read(sharedPreferencesProvider).setBool(_key, skipped);
  }
}
