import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/core/desktop/desktop_host.dart';
import 'package:sado/features/account/presentation/pages/sign_in_page.dart';
import 'package:sado/features/account/presentation/providers/account_providers.dart';
import 'package:sado/features/home/presentation/pages/home_page.dart';
import 'package:sado/features/memory/presentation/pages/memories_page.dart';
import 'package:sado/features/onboarding/presentation/pages/onboarding_page.dart';
import 'package:sado/features/onboarding/presentation/providers/onboarding_providers.dart';

abstract final class AppRoutes {
  static const home = '/';
  static const memories = '/memories';
  static const welcome = '/welcome';
  static const signIn = '/sign-in';
}

final appRouterProvider = Provider<GoRouter>(
  (ref) => GoRouter(
    redirect: (context, state) {
      final onWelcome = state.matchedLocation == AppRoutes.welcome;
      // The phone walkthrough has no place on a computer, where Sado waits
      // hidden in the tray.
      final needsWelcome =
          !ref.read(isDesktopProvider) && !ref.read(onboardingDoneProvider);
      if (needsWelcome && !onWelcome) {
        return AppRoutes.welcome;
      }
      // After the introduction, the phone asks once whether to sign in.
      final needsAccount =
          !needsWelcome &&
          ref.read(accountServiceProvider).supported &&
          ref.read(accountServiceProvider).current == null &&
          !ref.read(accountSkippedProvider);
      final onSignIn = state.matchedLocation == AppRoutes.signIn;
      if (needsAccount && !onSignIn && !onWelcome) return AppRoutes.signIn;
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.home,
        builder: (context, state) => const HomePage(),
      ),
      GoRoute(
        path: AppRoutes.memories,
        builder: (context, state) => const MemoriesPage(),
      ),
      GoRoute(
        path: AppRoutes.signIn,
        builder: (context, state) => const SignInPage(),
      ),
      GoRoute(
        path: AppRoutes.welcome,
        builder: (context, state) => const OnboardingPage(),
      ),
    ],
  ),
);
