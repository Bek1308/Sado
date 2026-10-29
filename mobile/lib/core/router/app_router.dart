import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/features/home/presentation/pages/home_page.dart';
import 'package:sado/features/memory/presentation/pages/memories_page.dart';
import 'package:sado/features/onboarding/presentation/pages/onboarding_page.dart';
import 'package:sado/features/onboarding/presentation/providers/onboarding_providers.dart';

abstract final class AppRoutes {
  static const home = '/';
  static const memories = '/memories';
  static const welcome = '/welcome';
}

final appRouterProvider = Provider<GoRouter>(
  (ref) => GoRouter(
    redirect: (context, state) {
      final onWelcome = state.matchedLocation == AppRoutes.welcome;
      if (!ref.read(onboardingDoneProvider) && !onWelcome) {
        return AppRoutes.welcome;
      }
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
        path: AppRoutes.welcome,
        builder: (context, state) => const OnboardingPage(),
      ),
    ],
  ),
);
