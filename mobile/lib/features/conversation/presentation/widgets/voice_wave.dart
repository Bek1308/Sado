import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/audioplayers_output.dart';
import 'package:sado/core/theme/app_theme.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';

/// A rolling picture of the voice in the room: the user's while Sado
/// listens, Sado's own while it speaks, a slow breath while it waits.
class VoiceWave extends ConsumerStatefulWidget {
  const VoiceWave({this.height = 56, super.key});

  final double height;

  @override
  ConsumerState<VoiceWave> createState() => _VoiceWaveState();
}

class _VoiceWaveState extends ConsumerState<VoiceWave>
    with SingleTickerProviderStateMixin {
  static const _bars = 40;

  /// New samples join the wave this often; slower reads as calmer.
  static const _sampleEvery = Duration(milliseconds: 45);

  late final Ticker _ticker;
  final _levels = List<double>.filled(_bars, 0);
  StreamSubscription<double>? _voice;
  double _voiceLevel = 0;
  Duration _lastSample = Duration.zero;
  Duration _now = Duration.zero;

  @override
  void initState() {
    super.initState();
    _voice = ref
        .read(audioOutputProvider)
        .loudness
        .listen((level) => _voiceLevel = level);
    _ticker = createTicker(_tick);
    unawaited(_ticker.start());
  }

  @override
  void dispose() {
    _ticker.dispose();
    unawaited(_voice?.cancel());
    super.dispose();
  }

  void _tick(Duration elapsed) {
    _now = elapsed;
    if (elapsed - _lastSample < _sampleEvery) return;
    _lastSample = elapsed;
    final mic = ref.read(micLevelProvider);
    final level = math.max(mic, _voiceLevel);
    // A little jitter keeps neighbouring bars from looking copied.
    final jitter = 0.85 + 0.3 * math.Random().nextDouble();
    setState(() {
      _levels
        ..removeAt(0)
        ..add((level * jitter).clamp(0.0, 1.0));
    });
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.height,
      width: double.infinity,
      child: CustomPaint(
        painter: _WavePainter(
          levels: List.of(_levels),
          breath: _now.inMilliseconds / 1000,
          rest: Theme.of(context).colorScheme.outlineVariant,
        ),
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  const _WavePainter({
    required this.levels,
    required this.breath,
    required this.rest,
  });

  final List<double> levels;

  /// Seconds since the wave started, for the idle breathing.
  final double breath;
  final Color rest;

  @override
  void paint(Canvas canvas, Size size) {
    final gap = size.width / levels.length;
    final barWidth = gap * 0.55;
    final middle = size.height / 2;
    final shader = const LinearGradient(
      colors: AppTheme.brandGradient,
    ).createShader(Offset.zero & size);
    final active = Paint()..shader = shader;
    final quiet = Paint()..color = rest;

    for (var bar = 0; bar < levels.length; bar++) {
      final idle = 0.06 + 0.04 * math.sin(breath * 2 + bar * 0.35);
      final level = math.max(levels[bar], idle);
      final height = math.max(level * size.height * 0.95, barWidth);
      final rect = RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: Offset(gap * (bar + 0.5), middle),
          width: barWidth,
          height: height,
        ),
        Radius.circular(barWidth / 2),
      );
      canvas.drawRRect(rect, levels[bar] > 0.05 ? active : quiet);
    }
  }

  @override
  bool shouldRepaint(_WavePainter old) =>
      old.breath != breath || old.levels != levels;
}
