import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/listening/presentation/widgets/mic_button.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/widgets/expression_cue_bar.dart';
import 'package:sado/features/voices/presentation/providers/voice_providers.dart';
import 'package:sado/features/voices/presentation/widgets/voice_picker.dart';

class SpeakPanel extends ConsumerStatefulWidget {
  const SpeakPanel({super.key});

  @override
  ConsumerState<SpeakPanel> createState() => _SpeakPanelState();
}

class _SpeakPanelState extends ConsumerState<SpeakPanel> {
  final _textController = TextEditingController();
  SpokenLanguage _language = SpokenLanguage.tajik;
  Mood _mood = Mood.neutral;

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _speak() async {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    await _say(text);
  }

  Future<void> _ask() async {
    final question = _textController.text.trim();
    if (question.isEmpty) return;
    _textController.clear();
    final reply = await ref
        .read(conversationControllerProvider.notifier)
        .ask(question, _language);
    if (reply != null && mounted) await _say(reply);
  }

  Future<void> _say(String text) => ref
      .read(speakControllerProvider.notifier)
      .speak(
        text,
        _language,
        voiceId: ref.read(selectedVoiceIdProvider),
        mood: _mood,
      );

  @override
  Widget build(BuildContext context) {
    final speaking = ref.watch(speakControllerProvider);
    final busy =
        speaking.isLoading ||
        ref.watch(conversationControllerProvider).isThinking;
    final error = speaking.error;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12,
      children: [
        const VoicePicker(),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final mood in Mood.values)
              ChoiceChip(
                avatar: Text(mood.emoji),
                label: Text(mood.label),
                selected: mood == _mood,
                onSelected: (_) => setState(() => _mood = mood),
              ),
          ],
        ),
        SegmentedButton<SpokenLanguage>(
          segments: [
            for (final language in SpokenLanguage.values)
              ButtonSegment(value: language, label: Text(language.nativeName)),
          ],
          selected: {_language},
          showSelectedIcon: false,
          onSelectionChanged: (selection) =>
              setState(() => _language = selection.single),
        ),
        Row(
          spacing: 8,
          children: [
            Expanded(
              child: TextField(
                controller: _textController,
                minLines: 1,
                maxLines: 4,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _speak(),
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'Type, or tap the mic and talk',
                ),
              ),
            ),
            MicButton(
              language: _language,
              onHeard: (text) => _textController.text = text,
            ),
          ],
        ),
        ExpressionCueBar(controller: _textController),
        Row(
          spacing: 8,
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: busy ? null : _speak,
                icon: speaking.isLoading
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.record_voice_over),
                label: const Text('Speak it'),
              ),
            ),
            Expanded(
              child: FilledButton.icon(
                onPressed: busy ? null : _ask,
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Ask Sado'),
              ),
            ),
          ],
        ),
        if (error != null)
          Text(
            error is Failure ? error.message : 'Something went wrong',
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
      ],
    );
  }
}
