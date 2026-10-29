import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/lists/domain/entities/sado_list.dart';
import 'package:sado/features/lists/presentation/providers/list_providers.dart';

/// The lists Sado keeps by voice; ticking an entry crosses it off.
class ListsView extends ConsumerWidget {
  const ListsView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return switch (ref.watch(listsControllerProvider)) {
      AsyncData(:final value) when value.isEmpty => const _NoLists(),
      AsyncData(:final value) => ListView.separated(
        padding: const EdgeInsets.all(AppSpacing.lg),
        itemCount: value.length,
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
        itemBuilder: (context, index) => _ListCard(list: value[index]),
      ),
      AsyncError(:final error) => _LoadFailed(
        message: error is Failure
            ? error.message
            : 'Lists could not be loaded.',
        onRetry: () => ref.invalidate(listsControllerProvider),
      ),
      _ => const Center(child: CircularProgressIndicator()),
    };
  }
}

class _ListCard extends ConsumerWidget {
  const _ListCard({required this.list});

  final SadoList list;

  Future<void> _crossOff(
    BuildContext context,
    WidgetRef ref,
    ListEntry entry,
  ) async {
    final problem = await ref
        .read(listsControllerProvider.notifier)
        .crossOff(entry);
    if (problem == null || !context.mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(problem)));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;

    return Card.outlined(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg,
                AppSpacing.sm,
                AppSpacing.lg,
                AppSpacing.xs,
              ),
              child: Row(
                spacing: AppSpacing.sm,
                children: [
                  Icon(Icons.checklist_rounded, color: colors.primary),
                  Expanded(
                    child: Text(
                      _title(list.name),
                      style: theme.textTheme.titleMedium,
                    ),
                  ),
                  Text(
                    '${list.entries.length}',
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: colors.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            for (final entry in list.entries)
              CheckboxListTile(
                value: false,
                controlAffinity: ListTileControlAffinity.leading,
                visualDensity: VisualDensity.compact,
                title: Text(entry.text),
                onChanged: (_) => _crossOff(context, ref, entry),
              ),
          ],
        ),
      ),
    );
  }

  /// Sado stores names in lower case so "Xarid" and "xarid" stay one list.
  static String _title(String name) =>
      name.isEmpty ? name : name[0].toUpperCase() + name.substring(1);
}

class _NoLists extends StatelessWidget {
  const _NoLists();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xxl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: AppSpacing.sm,
          children: [
            Icon(
              Icons.checklist_rounded,
              size: 56,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text('No lists yet', style: theme.textTheme.titleLarge),
            Text(
              'Ask Sado, for example: "Add bread and milk to my shopping '
              'list."',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _LoadFailed extends StatelessWidget {
  const _LoadFailed({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xxl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: AppSpacing.md,
          children: [
            Icon(
              Icons.cloud_off_outlined,
              size: 48,
              color: theme.colorScheme.error,
            ),
            Text(
              message,
              style: theme.textTheme.bodyLarge,
              textAlign: TextAlign.center,
            ),
            FilledButton.tonal(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
