import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/features/home/presentation/pages/home_page.dart';
import 'package:sado/features/memory/presentation/pages/memories_page.dart';

abstract final class AppRoutes {
  static const home = '/';
  static const memories = '/memories';
}

final appRouterProvider = Provider<GoRouter>(
  (ref) => GoRouter(
    routes: [
      GoRoute(
        path: AppRoutes.home,
        builder: (context, state) => const HomePage(),
      ),
      GoRoute(
        path: AppRoutes.memories,
        builder: (context, state) => const MemoriesPage(),
      ),
    ],
  ),
);
