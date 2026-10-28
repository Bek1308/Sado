import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/server_status/presentation/providers/server_status_providers.dart';

/// Appears only when Sado cannot be reached, and says how to recover.
class ServerStatusBanner extends ConsumerWidget {
  const ServerStatusBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final message = switch (ref.watch(serverStatusProvider)) {
      AsyncData(value: Err(:final failure)) => failure.message,
      AsyncError() => 'Something went wrong',
      _ => null,
    };
    if (message == null) return const SizedBox.shrink();

    final theme = Theme.of(context);
    final colors = theme.colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.lg,
        AppSpacing.sm,
        AppSpacing.lg,
        0,
      ),
      child: Material(
        color: colors.errorContainer,
        borderRadius: BorderRadius.circular(AppRadius.md),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.xs,
            AppSpacing.xs,
            AppSpacing.xs,
          ),
          child: Row(
            spacing: AppSpacing.md,
            children: [
              Icon(Icons.cloud_off_outlined, color: colors.onErrorContainer),
              Expanded(
                child: Text(
                  message,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: colors.onErrorContainer,
                  ),
                ),
              ),
              TextButton(
                onPressed: () => ref.invalidate(serverStatusProvider),
                style: TextButton.styleFrom(
                  foregroundColor: colors.onErrorContainer,
                ),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
