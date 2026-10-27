import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/failure.dart';
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
    await ref
        .read(speakControllerProvider.notifier)
        .speak(
          text,
          _language,
          voiceId: ref.read(selectedVoiceIdProvider),
          mood: _mood,
        );
  }

  @override
  Widget build(BuildContext context) {
    final speaking = ref.watch(speakControllerProvider);
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
        TextField(
          controller: _textController,
          minLines: 1,
          maxLines: 4,
          textInputAction: TextInputAction.send,
          onSubmitted: (_) => _speak(),
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'Type something for Sado to say',
          ),
        ),
        ExpressionCueBar(controller: _textController),
        FilledButton.icon(
          onPressed: speaking.isLoading ? null : _speak,
          icon: speaking.isLoading
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.record_voice_over),
          label: const Text('Speak'),
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
