import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/storage/preferences.dart';

final onboardingDoneProvider = NotifierProvider<OnboardingDone, bool>(
  OnboardingDone.new,
);

/// Whether the user has seen the introduction; it is shown once per install.
class OnboardingDone extends Notifier<bool> {
  static const _key = 'onboarding_done';

  @override
  bool build() => ref.watch(sharedPreferencesProvider).getBool(_key) ?? false;

  Future<void> finish() async {
    state = true;
    await ref.read(sharedPreferencesProvider).setBool(_key, true);
  }
}
