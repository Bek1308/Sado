import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/lists/presentation/widgets/lists_view.dart';
import 'package:sado/features/memory/domain/entities/memory.dart';
import 'package:sado/features/memory/presentation/providers/memory_providers.dart';

/// Everything Sado keeps for the user: facts it remembers and the lists it
/// manages by voice. The user can review, add to and delete all of it.
class MemoriesPage extends StatelessWidget {
  const MemoriesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Builder(
        builder: (context) {
          final tabs = DefaultTabController.of(context);
          return Scaffold(
            appBar: AppBar(
              title: const Text('Memories & lists'),
              bottom: const TabBar(
                tabs: [
                  Tab(text: 'Memories'),
                  Tab(text: 'Lists'),
                ],
              ),
            ),
            // Only memories are added by hand; lists are kept by voice.
            floatingActionButton: ListenableBuilder(
              listenable: tabs,
              builder: (context, _) =>
                  tabs.index == 0 ? const _AddMemoryButton() : const SizedBox(),
            ),
            body: Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: AppLayout.maxContentWidth,
                ),
                child: const TabBarView(
                  children: [_MemoriesTab(), ListsView()],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _AddMemoryButton extends ConsumerWidget {
  const _AddMemoryButton();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FloatingActionButton.extended(
      onPressed: () => _add(context, ref),
      icon: const Icon(Icons.add),
      label: const Text('Add memory'),
    );
  }

  Future<void> _add(BuildContext context, WidgetRef ref) async {
    final text = await showDialog<String>(
      context: context,
      builder: (context) => const _AddMemoryDialog(),
    );
    if (text == null || text.trim().isEmpty) return;

    final problem = await ref
        .read(memoriesControllerProvider.notifier)
        .remember(text);
    if (problem != null && context.mounted) _tell(context, problem);
  }
}

class _MemoriesTab extends ConsumerWidget {
  const _MemoriesTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return switch (ref.watch(memoriesControllerProvider)) {
      AsyncData(:final value) when value.isEmpty => const _Empty(),
      AsyncData(:final value) => _MemoryList(memories: value),
      AsyncError(:final error) => _LoadFailed(
        message: error is Failure
            ? error.message
            : 'Memories could not be loaded.',
        onRetry: () => ref.invalidate(memoriesControllerProvider),
      ),
      _ => const Center(child: CircularProgressIndicator()),
    };
  }
}

void _tell(BuildContext context, String message) =>
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));

class _MemoryList extends ConsumerWidget {
  const _MemoryList({required this.memories});

  final List<Memory> memories;

  // Leaves room under the last card for the floating button.
  static const _bottomPadding = 96.0;

  Future<void> _forget(
    BuildContext context,
    WidgetRef ref,
    Memory memory,
  ) async {
    final problem = await ref
        .read(memoriesControllerProvider.notifier)
        .forget(memory);
    if (!context.mounted) return;
    _tell(context, problem ?? 'Sado forgot it.');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.lg,
        AppSpacing.sm,
        AppSpacing.lg,
        _bottomPadding,
      ),
      itemCount: memories.length,
      separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
      itemBuilder: (context, index) {
        final memory = memories[index];
        return Dismissible(
          key: ValueKey(memory.id),
          direction: DismissDirection.endToStart,
          background: const _DeleteBackground(),
          onDismissed: (_) => _forget(context, ref, memory),
          child: _MemoryCard(
            memory: memory,
            onForget: () => _forget(context, ref, memory),
          ),
        );
      },
    );
  }
}

class _MemoryCard extends StatelessWidget {
  const _MemoryCard({required this.memory, required this.onForget});

  final Memory memory;
  final VoidCallback onForget;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;

    return Card.outlined(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.lg,
          AppSpacing.md,
          AppSpacing.xs,
          AppSpacing.md,
        ),
        child: Row(
          spacing: AppSpacing.md,
          children: [
            Icon(Icons.bookmark_outline, color: colors.primary),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: AppSpacing.xs,
                children: [
                  Text(memory.text, style: theme.textTheme.bodyLarge),
                  Text(
                    _savedOn(memory.createdAt),
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: colors.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              tooltip: 'Forget',
              icon: const Icon(Icons.delete_outline),
              color: colors.onSurfaceVariant,
              onPressed: onForget,
            ),
          ],
        ),
      ),
    );
  }
}

const _months = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

String _savedOn(DateTime moment) =>
    'Saved ${moment.day} ${_months[moment.month - 1]} ${moment.year}';

class _DeleteBackground extends StatelessWidget {
  const _DeleteBackground();

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: colors.errorContainer,
        borderRadius: BorderRadius.circular(AppRadius.sm),
      ),
      child: Align(
        alignment: Alignment.centerRight,
        child: Padding(
          padding: const EdgeInsets.only(right: AppSpacing.xl),
          child: Icon(Icons.delete_outline, color: colors.onErrorContainer),
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty();

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
              Icons.bookmarks_outlined,
              size: 56,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text('Nothing saved yet', style: theme.textTheme.titleLarge),
            Text(
              'Add a fact here, or long-press one of your messages in the '
              'chat and choose "Remember this".',
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

class _AddMemoryDialog extends StatefulWidget {
  const _AddMemoryDialog();

  @override
  State<_AddMemoryDialog> createState() => _AddMemoryDialogState();
}

class _AddMemoryDialogState extends State<_AddMemoryDialog> {
  static const _maxLength = 500;

  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _save() => Navigator.of(context).pop(_controller.text);

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add memory'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        minLines: 2,
        maxLines: 5,
        maxLength: _maxLength,
        textCapitalization: TextCapitalization.sentences,
        decoration: InputDecoration(
          hintText: 'e.g. My daughter’s birthday is 12 May',
          // The dialog shares the field's usual fill, which would hide it.
          fillColor: Theme.of(context).colorScheme.surfaceContainerLowest,
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ValueListenableBuilder(
          valueListenable: _controller,
          builder: (context, value, _) => FilledButton(
            onPressed: value.text.trim().isEmpty ? null : _save,
            child: const Text('Save'),
          ),
        ),
      ],
    );
  }
}
