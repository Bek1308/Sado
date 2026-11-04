import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/core/theme/app_theme.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_settings_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/home/presentation/widgets/mode_switcher.dart';
import 'package:sado/features/listening/presentation/widgets/mic_button.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';
import 'package:sado/features/speech/presentation/widgets/expression_cue_button.dart';
import 'package:sado/features/vision/presentation/widgets/camera_button.dart';

/// Where the user talks or types to Sado.
///
/// With an empty field the main action is the mic; once there is text it
/// becomes send.
class Composer extends ConsumerStatefulWidget {
  const Composer({super.key});

  @override
  ConsumerState<Composer> createState() => _ComposerState();
}

class _ComposerState extends ConsumerState<Composer> {
  final _textController = TextEditingController();

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _ask(String text) async {
    final question = text.trim();
    if (question.isEmpty) return;
    _textController.clear();
    final reply = await ref
        .read(conversationControllerProvider.notifier)
        .ask(
          question,
          ref.read(spokenLanguageProvider),
          ref.read(sadoModeProvider),
        );
    await _voiceReply(reply);
  }

  Future<void> _voiceReply(SadoReply? reply) async {
    if (reply == null || !mounted) return;
    await ref.read(speakControllerProvider.notifier).say(reply.text);
  }

  Future<void> _showExplanation(String text) async {
    ref.read(conversationControllerProvider.notifier).showExplanation(text);
    await ref.read(speakControllerProvider.notifier).say(text);
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(liveConversationProvider, (_, live) {
      if (live.error != null && context.mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(live.error!)));
      }
    });
    final thinking = ref.watch(
      conversationControllerProvider.select((state) => state.isThinking),
    );
    final voicing = ref.watch(speakControllerProvider).isLoading;
    final live = ref.watch(liveConversationProvider);
    final hint = switch (live.phase) {
      LivePhase.listening => 'Listening…',
      LivePhase.thinking => 'Thinking…',
      LivePhase.speaking => 'Speaking…',
      LivePhase.idle => 'Message Sado',
    };

    final colors = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.xs,
        AppSpacing.md,
        AppSpacing.md,
      ),
      child: ValueListenableBuilder(
        valueListenable: _textController,
        builder: (context, value, _) {
          final hasText = value.text.trim().isNotEmpty;

          return Column(
            mainAxisSize: MainAxisSize.min,
            spacing: AppSpacing.sm,
            children: [
              const ModeSwitcher(),
              // One floating card holds the words and every way to send
              // them, like the composers people know from AI chat apps.
              DecoratedBox(
                decoration: BoxDecoration(
                  color: colors.surfaceContainerHigh,
                  borderRadius: BorderRadius.circular(28),
                  border: Border.all(
                    color: colors.outlineVariant.withValues(alpha: 0.4),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.12),
                      blurRadius: 24,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                    AppSpacing.xs,
                    AppSpacing.xs,
                    AppSpacing.sm,
                    AppSpacing.sm,
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TextField(
                        controller: _textController,
                        minLines: 1,
                        maxLines: 5,
                        textCapitalization: TextCapitalization.sentences,
                        textInputAction: TextInputAction.send,
                        onSubmitted: thinking ? null : _ask,
                        decoration: InputDecoration(
                          hintText: hint,
                          filled: false,
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.fromLTRB(
                            AppSpacing.md,
                            AppSpacing.md,
                            AppSpacing.md,
                            AppSpacing.xs,
                          ),
                        ),
                      ),
                      Row(
                        children: [
                          ExpressionCueButton(controller: _textController),
                          CameraButton(onExplained: _showExplanation),
                          if (hasText)
                            IconButton(
                              tooltip: 'Read aloud',
                              icon: const Icon(Icons.volume_up_outlined),
                              onPressed: voicing
                                  ? null
                                  : () => ref
                                        .read(speakControllerProvider.notifier)
                                        .say(value.text.trim()),
                            ),
                          const Spacer(),
                          // While live, the mic button is the only way to
                          // stop it.
                          if (hasText && !live.isLive)
                            _SendButton(
                              onPressed: thinking
                                  ? null
                                  : () => _ask(value.text),
                            )
                          else
                            const MicButton(),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

/// Sends the typed message, in Sado's colours.
class _SendButton extends StatelessWidget {
  const _SendButton({required this.onPressed});

  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: MicButton.size,
      child: DecoratedBox(
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: AppTheme.brandGradient,
          ),
        ),
        child: IconButton(
          tooltip: 'Send',
          color: Colors.white,
          icon: const Icon(Icons.arrow_upward_rounded),
          onPressed: onPressed,
        ),
      ),
    );
  }
}
