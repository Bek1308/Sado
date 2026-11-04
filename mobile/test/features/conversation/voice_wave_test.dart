import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/audio/audio_output.dart';
import 'package:sado/core/audio/audioplayers_output.dart';
import 'package:sado/features/conversation/presentation/widgets/voice_wave.dart';

final class _SilentAudio implements AudioOutput {
  @override
  Future<void> playWav(Uint8List wavBytes) async {}

  @override
  Future<void> stop() async {}

  @override
  Stream<double> get loudness => const Stream.empty();
}

void main() {
  testWidgets('keeps rolling new samples in without failing', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [audioOutputProvider.overrideWithValue(_SilentAudio())],
        child: const MaterialApp(home: Scaffold(body: VoiceWave())),
      ),
    );

    // Many sample periods, so the oldest bar is dropped again and again.
    for (var frame = 0; frame < 20; frame++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(tester.takeException(), isNull);
    expect(find.byType(VoiceWave), findsOneWidget);
  });
}
