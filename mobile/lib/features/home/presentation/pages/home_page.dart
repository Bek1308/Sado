import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/router/app_router.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/widgets/conversation_view.dart';
import 'package:sado/features/home/presentation/widgets/composer.dart';
import 'package:sado/features/home/presentation/widgets/home_app_bar.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/server_status/presentation/widgets/server_status_banner.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/vision/presentation/providers/vision_providers.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    _reportProblems(context, ref);

    return Scaffold(
      // The composer follows the keyboard itself, so the conversation keeps
      // its height and only the input moves.
      resizeToAvoidBottomInset: false,
      appBar: const HomeAppBar(),
      body: const _ContentWidth(
        child: Column(
          children: [
            ServerStatusBanner(),
            Expanded(child: ConversationView()),
          ],
        ),
      ),
      bottomNavigationBar: Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.viewInsetsOf(context).bottom,
        ),
        child: const SafeArea(
          top: false,
          child: _ContentWidth(child: Composer()),
        ),
      ),
    );
  }

  /// Problems are shown once, as they happen, instead of lingering on screen.
  void _reportProblems(BuildContext context, WidgetRef ref) {
    void show(String message) => ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));

    ref
      ..listen(speakControllerProvider, (_, next) {
        if (next case AsyncError(:final error)) {
          show(error is Failure ? error.message : 'Sado could not speak');
        }
      })
      ..listen(listeningControllerProvider, (_, next) {
        if (next case ListeningFailed(:final message)) show(message);
      })
      ..listen(visionControllerProvider, (_, next) {
        if (next case VisionFailed(:final message)) show(message);
      })
      ..listen(conversationControllerProvider, (previous, next) {
        final error = next.error;
        if (error != null && error != previous?.error) show(error);
        final reply = next.lastReply;
        if (reply != null && !identical(reply, previous?.lastReply)) {
          _confirmActions(context, reply);
        }
      });
  }
}

/// One note for everything Sado just did, with a way to see it.
void _confirmActions(BuildContext context, SadoReply reply) {
  final notes = [
    if (reply.remembered.isNotEmpty)
      'Remembered: ${reply.remembered.join(', ')}',
    if (reply.reminded.isNotEmpty) 'Reminder: ${reply.reminded.join(', ')}',
    if (reply.listsChanged) 'List updated',
  ];
  if (notes.isEmpty) return;
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(
      SnackBar(
        content: Text(notes.join('\n')),
        action: SnackBarAction(
          label: 'View',
          onPressed: () => context.push(AppRoutes.memories),
        ),
      ),
    );
}

class _ContentWidth extends StatelessWidget {
  const _ContentWidth({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      heightFactor: 1,
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          maxWidth: AppLayout.maxContentWidth,
        ),
        child: child,
      ),
    );
  }
}
