import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/router/app_router.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/core/theme/app_theme.dart';
import 'package:sado/core/widgets/sado_orb.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/server_status/presentation/providers/server_status_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/widgets/voice_style_sheet.dart';

class HomeAppBar extends ConsumerWidget implements PreferredSizeWidget {
  const HomeAppBar({super.key});

  static const _height = 64.0;

  @override
  Size get preferredSize => const Size.fromHeight(_height);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hasConversation = ref.watch(
      conversationControllerProvider.select(
        (state) => state.messages.isNotEmpty,
      ),
    );

    return AppBar(
      toolbarHeight: _height,
      titleSpacing: AppSpacing.lg,
      title: const Row(
        spacing: AppSpacing.md,
        children: [
          SadoOrb(size: 36),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [Text('Sado'), _StatusLine()],
          ),
        ],
      ),
      actions: [
        if (hasConversation)
          IconButton(
            tooltip: 'New conversation',
            icon: const Icon(Icons.add_comment_outlined),
            onPressed: () =>
                ref.read(conversationControllerProvider.notifier).startOver(),
          ),
        IconButton(
          tooltip: 'Memories',
          icon: const Icon(Icons.bookmarks_outlined),
          onPressed: () => context.push(AppRoutes.memories),
        ),
        IconButton(
          tooltip: 'Voice & style',
          icon: const Icon(Icons.tune),
          onPressed: () => showVoiceStyleSheet(context),
        ),
        const SizedBox(width: AppSpacing.sm),
      ],
    );
  }
}

/// What Sado is doing right now; falls back to whether it can be reached.
class _StatusLine extends ConsumerWidget {
  const _StatusLine();

  static const _dotSize = 8.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    final live = ref.watch(liveConversationProvider).phase;
    final listening = ref.watch(listeningControllerProvider);
    final thinking = ref.watch(
      conversationControllerProvider.select((state) => state.isThinking),
    );
    final voicing = ref.watch(speakControllerProvider).isLoading;
    final server = ref.watch(serverStatusProvider);

    final (label, color) = switch ((
      live,
      listening,
      thinking,
      voicing,
      server,
    )) {
      (LivePhase.listening, _, _, _, _) => ('Listening…', colors.error),
      (LivePhase.thinking, _, _, _, _) => ('Thinking…', colors.primary),
      (LivePhase.speaking, _, _, _, _) => ('Speaking…', colors.primary),
      (_, ListeningRecording(), _, _, _) => ('Listening…', colors.error),
      (_, ListeningTranscribing(), _, _, _) => (
        'Transcribing…',
        colors.primary,
      ),
      (_, _, true, _, _) => ('Thinking…', colors.primary),
      (_, _, _, true, _) => ('Preparing voice…', colors.primary),
      (_, _, _, _, AsyncData(value: Ok())) => ('Online', AppTheme.onlineColor),
      (_, _, _, _, AsyncData() || AsyncError()) => ('Offline', colors.error),
      _ => ('Connecting…', colors.outline),
    };

    return Row(
      mainAxisSize: MainAxisSize.min,
      spacing: AppSpacing.sm,
      children: [
        Container(
          width: _dotSize,
          height: _dotSize,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: colors.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}
