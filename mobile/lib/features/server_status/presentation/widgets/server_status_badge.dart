import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/server_status/presentation/providers/server_status_providers.dart';

class ServerStatusBadge extends ConsumerWidget {
  const ServerStatusBadge({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = Theme.of(context).colorScheme;
    final status = ref.watch(serverStatusProvider);

    final (label, color) = switch (status) {
      AsyncData(value: Ok(:final value)) => (
        'Connected · v${value.version}',
        colors.primary,
      ),
      AsyncData(value: Err(:final failure)) => (failure.message, colors.error),
      AsyncError() => ('Unexpected error', colors.error),
      _ => ('Connecting…', colors.outline),
    };

    return ActionChip(
      avatar: Icon(Icons.circle, size: 10, color: color),
      label: Text(label),
      onPressed: () => ref.invalidate(serverStatusProvider),
    );
  }
}
