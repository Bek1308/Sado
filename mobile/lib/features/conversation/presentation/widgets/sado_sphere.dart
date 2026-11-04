import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/audio/audioplayers_output.dart';
import 'package:sado/core/theme/app_theme.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';

/// Sado as a living 3D sphere. Its surface ripples with the voice: the
/// user's while Sado listens, Sado's own while it speaks. It turns violet
/// when Sado talks and its colours swirl while it thinks.
class SadoSphere extends ConsumerStatefulWidget {
  const SadoSphere({required this.size, super.key});

  final double size;

  @override
  ConsumerState<SadoSphere> createState() => _SadoSphereState();
}

class _SadoSphereState extends ConsumerState<SadoSphere>
    with SingleTickerProviderStateMixin {
  static Future<ui.FragmentProgram?>? _program;

  /// How quickly the drawn values follow the voice; higher is snappier.
  static const _follow = 10.0;

  late final Ticker _ticker = createTicker(_tick);
  StreamSubscription<double>? _loudness;
  ui.FragmentShader? _shader;
  Duration _elapsed = Duration.zero;
  double _spoken = 0;
  double _level = 0;
  double _mood = 0;
  double _think = 0;

  @override
  void initState() {
    super.initState();
    _program ??=
        ui.FragmentProgram.fromAsset(
              'shaders/sado_sphere.frag',
            )
            .then<ui.FragmentProgram?>((program) => program)
            .catchError(
              // Widget tests and GPUs without shaders get the flat sphere.
              (Object _) => null,
            );
    unawaited(
      _program!.then((program) {
        if (mounted && program != null) {
          setState(() => _shader = program.fragmentShader());
        }
      }),
    );
    _loudness = ref
        .read(audioOutputProvider)
        .loudness
        .listen(
          (level) => _spoken = level,
        );
    unawaited(_ticker.start());
  }

  void _tick(Duration elapsed) {
    final step = (elapsed - _elapsed).inMicroseconds / 1e6;
    _elapsed = elapsed;
    final phase = ref.read(liveConversationProvider).phase;
    final thinking =
        phase == LivePhase.thinking ||
        ref.read(conversationControllerProvider).isThinking;
    final speaking = phase == LivePhase.speaking || _spoken > 0.02;
    final seconds = elapsed.inMicroseconds / 1e6;
    final target = switch ((speaking, phase)) {
      (true, _) => _spoken,
      (_, LivePhase.listening) => ref.read(micLevelProvider),
      // A slow breath while waiting or thinking, so Sado never looks dead.
      _ => 0.12 + 0.06 * math.sin(seconds * 2),
    };
    final blend = 1 - math.exp(-_follow * step);
    setState(() {
      _level += (target - _level) * blend;
      _mood += ((speaking ? 1.0 : 0.0) - _mood) * blend * 0.5;
      _think += ((thinking ? 1.0 : 0.0) - _think) * blend * 0.5;
    });
  }

  @override
  void dispose() {
    _ticker.dispose();
    unawaited(_loudness?.cancel());
    _shader?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final shader = _shader;
    // Large times lose precision on phone GPUs; the shader's motion repeats
    // every 20π seconds, so wrapping there is invisible.
    final time = (_elapsed.inMicroseconds / 1e6) % (20 * math.pi);
    return Semantics(
      label: 'Sado',
      child: SizedBox.square(
        dimension: widget.size,
        child: shader == null
            ? _FlatSphere(level: _level)
            : CustomPaint(
                painter: _SpherePainter(
                  shader: shader,
                  time: time,
                  level: _level,
                  mood: _mood,
                  think: _think,
                ),
              ),
      ),
    );
  }
}

class _SpherePainter extends CustomPainter {
  _SpherePainter({
    required this.shader,
    required this.time,
    required this.level,
    required this.mood,
    required this.think,
  });

  final ui.FragmentShader shader;
  final double time;
  final double level;
  final double mood;
  final double think;

  @override
  void paint(Canvas canvas, Size size) {
    shader
      ..setFloat(0, size.width)
      ..setFloat(1, size.height)
      ..setFloat(2, time)
      ..setFloat(3, level.clamp(0, 1))
      ..setFloat(4, mood.clamp(0, 1))
      ..setFloat(5, think.clamp(0, 1));
    canvas.drawRect(Offset.zero & size, Paint()..shader = shader);
  }

  @override
  bool shouldRepaint(_SpherePainter old) => true;
}

/// The sphere for devices that cannot run the shader: a breathing gradient.
class _FlatSphere extends StatelessWidget {
  const _FlatSphere({required this.level});

  final double level;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: FractionallySizedBox(
        widthFactor: 0.62 + 0.12 * level,
        heightFactor: 0.62 + 0.12 * level,
        child: DecoratedBox(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const RadialGradient(
              center: Alignment(-0.35, -0.4),
              colors: AppTheme.brandGradient,
            ),
            boxShadow: [
              BoxShadow(
                color: AppTheme.brandGradient.last.withValues(alpha: 0.45),
                blurRadius: 40 + 40 * level,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
