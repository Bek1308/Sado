import 'package:flutter/material.dart';
import 'package:sado/features/server_status/presentation/widgets/server_status_badge.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  static const _orbSize = 160.0;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            spacing: 24,
            children: [
              Container(
                width: _orbSize,
                height: _orbSize,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      theme.colorScheme.primary,
                      theme.colorScheme.primaryContainer,
                    ],
                  ),
                ),
                child: Icon(
                  Icons.graphic_eq,
                  size: _orbSize / 2,
                  color: theme.colorScheme.onPrimary,
                ),
              ),
              Text('Sado', style: theme.textTheme.displayMedium),
              Text(
                'One voice. Every language.',
                style: theme.textTheme.titleMedium,
              ),
              const ServerStatusBadge(),
            ],
          ),
        ),
      ),
    );
  }
}
