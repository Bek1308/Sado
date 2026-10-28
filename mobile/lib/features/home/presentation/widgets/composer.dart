import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/listening/presentation/widgets/mic_button.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';
import 'package:sado/features/speech/presentation/widgets/expression_cue_button.dart';

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
        .ask(question, ref.read(spokenLanguageProvider));
    if (reply != null && mounted) {
      await ref.read(speakControllerProvider.notifier).say(reply);
    }
  }

  @override
  Widget build(BuildContext context) {
    final language = ref.watch(spokenLanguageProvider);
    final thinking = ref.watch(
      conversationControllerProvider.select((state) => state.isThinking),
    );
    final voicing = ref.watch(speakControllerProvider).isLoading;
    final hint = switch (ref.watch(listeningControllerProvider)) {
      ListeningRecording() => 'Listening…',
      ListeningTranscribing() => 'Transcribing…',
      _ => 'Message Sado',
    };

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.md,
      ),
      child: ValueListenableBuilder(
        valueListenable: _textController,
        builder: (context, value, _) {
          final hasText = value.text.trim().isNotEmpty;

          return Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            spacing: AppSpacing.sm,
            children: [
              Expanded(
                child: TextField(
                  controller: _textController,
                  minLines: 1,
                  maxLines: 5,
                  textCapitalization: TextCapitalization.sentences,
                  textInputAction: TextInputAction.send,
                  onSubmitted: thinking ? null : _ask,
                  decoration: InputDecoration(
                    hintText: hint,
                    prefixIcon: ExpressionCueButton(
                      controller: _textController,
                    ),
                    suffixIcon: hasText
                        ? IconButton(
                            tooltip: 'Read aloud',
                            icon: const Icon(Icons.volume_up_outlined),
                            onPressed: voicing
                                ? null
                                : () => ref
                                      .read(speakControllerProvider.notifier)
                                      .say(value.text.trim()),
                          )
                        : null,
                  ),
                ),
              ),
              if (hasText)
                SizedBox.square(
                  dimension: MicButton.size,
                  child: IconButton.filled(
                    tooltip: 'Send',
                    icon: const Icon(Icons.arrow_upward_rounded),
                    onPressed: thinking ? null : () => _ask(value.text),
                  ),
                )
              else
                MicButton(language: language, onHeard: _ask),
            ],
          );
        },
      ),
    );
  }
}
