import 'package:flutter/material.dart';
import 'package:sado/features/conversation/presentation/widgets/conversation_view.dart';
import 'package:sado/features/server_status/presentation/widgets/server_status_badge.dart';
import 'package:sado/features/speech/presentation/widgets/speak_panel.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  static const _orbSize = 140.0;
  static const _maxContentWidth = 520.0;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: _maxContentWidth),
              child: Column(
                spacing: 20,
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
                  const ConversationView(),
                  const SpeakPanel(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
