import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/desktop/desktop_host.dart';
import 'package:sado/core/router/app_router.dart';
import 'package:sado/core/theme/app_theme.dart';
import 'package:sado/features/desktop/presentation/widgets/desktop_shell.dart';

class SadoApp extends ConsumerWidget {
  const SadoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'Sado',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      routerConfig: ref.watch(appRouterProvider),
      debugShowCheckedModeBanner: false,
      builder: ref.watch(isDesktopProvider)
          ? (context, child) => DesktopShell(child: child!)
          : null,
    );
  }
}
