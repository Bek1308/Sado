import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/listening/presentation/providers/listening_providers.dart';
import 'package:sado/features/speech/domain/entities/mood.dart';
import 'package:sado/features/speech/presentation/providers/speech_providers.dart';
import 'package:sado/features/speech/presentation/providers/speech_settings_providers.dart';

/// Sado the robot: hovers, blinks its visor eyes, flashes its antenna and
/// talks through an equalizer mouth. Its glow follows the selected mood.
class SadoFace extends ConsumerStatefulWidget {
  const SadoFace({this.size = 120, super.key});

  final double size;

  @override
  ConsumerState<SadoFace> createState() => _SadoFaceState();
}

enum _Activity { idle, listening, thinking, speaking }

/// Every visual knob of the robot, so moods and states blend smoothly.
class _FaceParams {
  const _FaceParams({
    this.eyeOpen = 1,
    this.eyeSize = 1,
    this.gazeDX = 0,
    this.mouthActivity = 0,
    this.smile = 0.35,
    this.browTilt = 0,
    this.cheekGlow = 0,
    this.visor = const Color(0xFF38E1FF),
  });

  factory _FaceParams.lerp(_FaceParams a, _FaceParams b, double t) =>
      _FaceParams(
        eyeOpen: _mix(a.eyeOpen, b.eyeOpen, t),
        eyeSize: _mix(a.eyeSize, b.eyeSize, t),
        gazeDX: _mix(a.gazeDX, b.gazeDX, t),
        mouthActivity: _mix(a.mouthActivity, b.mouthActivity, t),
        smile: _mix(a.smile, b.smile, t),
        browTilt: _mix(a.browTilt, b.browTilt, t),
        cheekGlow: _mix(a.cheekGlow, b.cheekGlow, t),
        visor: Color.lerp(a.visor, b.visor, t) ?? a.visor,
      );

  final double eyeOpen;
  final double eyeSize;
  final double gazeDX;
  final double mouthActivity;
  final double smile;
  final double browTilt;
  final double cheekGlow;
  final Color visor;

  static double _mix(double a, double b, double t) => a + (b - a) * t;
}

class _SadoFaceState extends ConsumerState<SadoFace>
    with TickerProviderStateMixin {
  late final AnimationController _breathe;
  late final AnimationController _blink;
  late final AnimationController _morph;
  _FaceParams _from = const _FaceParams();
  _FaceParams _to = const _FaceParams();
  (Mood, _Activity)? _key;

  @override
  void initState() {
    super.initState();
    _breathe = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    );
    unawaited(_breathe.repeat(reverse: true));
    _blink = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 4200),
    );
    unawaited(_blink.repeat());
    _morph = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 450),
    );
  }

  /// Starts a morph toward [target] after this frame finishes.
  void _morphToward(_FaceParams target, (Mood, _Activity) key) {
    final from = _FaceParams.lerp(_from, _to, _morph.value);
    _key = key;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _from = from;
      _to = target;
      unawaited(_morph.forward(from: 0));
    });
  }

  /// Mood, activity and face parameters for the current app state.
  (Mood, _Activity, _FaceParams) _resolve(WidgetRef ref) {
    final mood = ref.watch(moodProvider);
    final speaking = ref.watch(speakControllerProvider).isLoading;
    final thinking = ref.watch(
      conversationControllerProvider.select((state) => state.isThinking),
    );
    final listening = switch (ref.watch(listeningControllerProvider)) {
      ListeningRecording() || ListeningTranscribing() => true,
      _ => false,
    };
    final activity = speaking
        ? _Activity.speaking
        : thinking
        ? _Activity.thinking
        : listening
        ? _Activity.listening
        : _Activity.idle;
    return (mood, activity, _blend(mood, activity));
  }

  @override
  void dispose() {
    _breathe.dispose();
    _blink.dispose();
    _morph.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final target = _resolve(ref);
    final key = (target.$1, target.$2);
    if (_key == null) {
      _from = _to = target.$3;
      _morph.value = 1;
      _key = key;
    } else if (key != _key) {
      _morphToward(target.$3, key);
    }
    return AnimatedBuilder(
      animation: Listenable.merge([_breathe, _blink, _morph]),
      builder: (context, _) {
        final params = _FaceParams.lerp(_from, _to, _morph.value);
        final activity = _key?.$2 ?? _Activity.idle;
        // A quick lid dip near the end of every blink cycle.
        final blinkPhase = (_blink.value - 0.9) / 0.1;
        final blink = blinkPhase <= 0
            ? 0.0
            : math.sin(blinkPhase * math.pi).clamp(0.0, 1.0);
        final flap = 0.5 + 0.5 * math.sin(_breathe.value * 2 * math.pi * 12);
        return CustomPaint(
          size: Size.square(widget.size),
          painter: _SadoFacePainter(
            params: params,
            blink: blink,
            hover: _breathe.value,
            mouthFlap: activity == _Activity.speaking ? flap : 0,
            thinkingDots: activity == _Activity.thinking,
          ),
        );
      },
    );
  }
}

_FaceParams _blend(Mood mood, _Activity activity) {
  var params = switch (mood) {
    Mood.neutral => const _FaceParams(),
    Mood.happy => const _FaceParams(
      eyeSize: 1.15,
      smile: 1,
      cheekGlow: 1,
      visor: Color(0xFF4ADE80),
    ),
    Mood.calm => const _FaceParams(
      eyeOpen: 0.7,
      smile: 0.3,
      visor: Color(0xFF7DD3FC),
    ),
    Mood.sad => const _FaceParams(
      eyeOpen: 0.8,
      smile: -0.8,
      browTilt: -1,
      visor: Color(0xFF60A5FA),
    ),
    Mood.excited => const _FaceParams(
      eyeSize: 1.25,
      smile: 0.9,
      cheekGlow: 0.6,
      visor: Color(0xFFFACC15),
    ),
    Mood.serious => const _FaceParams(
      eyeOpen: 0.85,
      smile: 0,
      browTilt: 1,
      visor: Color(0xFFF87171),
    ),
  };
  switch (activity) {
    case _Activity.speaking:
      params = _FaceParams(
        eyeOpen: params.eyeOpen,
        eyeSize: params.eyeSize,
        smile: params.smile,
        browTilt: params.browTilt,
        cheekGlow: params.cheekGlow,
        visor: params.visor,
        mouthActivity: 1,
      );
    case _Activity.thinking:
      params = _FaceParams(
        eyeSize: params.eyeSize,
        browTilt: params.browTilt,
        cheekGlow: params.cheekGlow,
        visor: params.visor,
        gazeDX: 0.6,
      );
    case _Activity.listening:
      params = _FaceParams(
        eyeSize: 1.2,
        smile: 0,
        browTilt: params.browTilt,
        cheekGlow: params.cheekGlow,
        visor: params.visor,
      );
    case _Activity.idle:
      break;
  }
  return params;
}

class _SadoFacePainter extends CustomPainter {
  const _SadoFacePainter({
    required this.params,
    required this.blink,
    required this.hover,
    required this.mouthFlap,
    required this.thinkingDots,
  });

  final _FaceParams params;
  final double blink;
  final double hover;
  final double mouthFlap;
  final bool thinkingDots;

  @override
  void paint(Canvas canvas, Size size) {
    final radius = size.shortestSide / 2;
    // The whole robot floats up and down.
    final center = size
        .center(Offset.zero)
        .translate(
          0,
          (hover - 0.5) * 2 * radius * 0.05,
        );
    final visor = params.visor;
    final pulse = 0.5 + 0.5 * math.sin(hover * 2 * math.pi * 2);

    _paintNeck(canvas, center, radius);
    _paintHead(canvas, center, radius);
    _paintAntenna(canvas, center, radius, visor, pulse);
    _paintEars(canvas, center, radius, visor);
    _paintVisor(canvas, center, radius, visor);
    _paintCheeks(canvas, center, radius, visor);
    _paintMouth(canvas, center, radius, visor);
  }

  void _paintNeck(Canvas canvas, Offset center, double radius) {
    final steel = Paint()..color = const Color(0xFF4A5A73);
    final top = center.dy + radius * 0.52;
    canvas
      ..drawPath(
        Path()
          ..moveTo(center.dx - radius * 0.18, top)
          ..lineTo(center.dx + radius * 0.18, top)
          ..lineTo(center.dx + radius * 0.3, top + radius * 0.22)
          ..lineTo(center.dx - radius * 0.3, top + radius * 0.22)
          ..close(),
        steel,
      )
      ..drawLine(
        Offset(center.dx - radius * 0.55, top + radius * 0.22),
        Offset(center.dx + radius * 0.55, top + radius * 0.22),
        steel
          ..strokeWidth = radius * 0.05
          ..strokeCap = StrokeCap.round,
      );
  }

  void _paintHead(Canvas canvas, Offset center, double radius) {
    final headCenter = Offset(center.dx, center.dy - radius * 0.05);
    final headRect = Rect.fromCenter(
      center: headCenter,
      width: radius * 1.5,
      height: radius * 1.25,
    );
    final head = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0xFFE8EEF5), Color(0xFF9FB2C8), Color(0xFF6B7F99)],
      ).createShader(headRect);
    // A glossy streak across the top.
    canvas
      ..drawRRect(
        RRect.fromRectAndRadius(headRect, Radius.circular(radius * 0.35)),
        head,
      )
      ..drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(
            center: Offset(headCenter.dx, headRect.top + radius * 0.12),
            width: radius * 1.1,
            height: radius * 0.18,
          ),
          Radius.circular(radius * 0.09),
        ),
        Paint()..color = Colors.white.withValues(alpha: 0.35),
      )
      ..drawRRect(
        RRect.fromRectAndRadius(headRect, Radius.circular(radius * 0.35)),
        Paint()
          ..color = const Color(0xFF4A5A73)
          ..style = PaintingStyle.stroke
          ..strokeWidth = radius * 0.03,
      );
  }

  void _paintAntenna(
    Canvas canvas,
    Offset center,
    double radius,
    Color visor,
    double pulse,
  ) {
    final top = center.dy - radius * 0.675;
    canvas.drawLine(
      Offset(center.dx, top + radius * 0.1),
      Offset(center.dx, top - radius * 0.14),
      Paint()
        ..color = const Color(0xFF4A5A73)
        ..strokeWidth = radius * 0.045
        ..strokeCap = StrokeCap.round,
    );
    final lamp = Offset(center.dx, top - radius * 0.22);
    canvas
      ..drawCircle(
        lamp,
        radius * 0.12,
        Paint()..color = visor.withValues(alpha: 0.25 + 0.35 * pulse),
      )
      ..drawCircle(lamp, radius * 0.07, Paint()..color = visor)
      ..drawCircle(
        lamp.translate(-radius * 0.02, -radius * 0.02),
        radius * 0.025,
        Paint()..color = Colors.white,
      );
  }

  void _paintEars(Canvas canvas, Offset center, double radius, Color visor) {
    for (final side in [-1.0, 1.0]) {
      final ear = Offset(center.dx + side * radius * 0.78, center.dy);
      canvas
        ..drawCircle(
          ear,
          radius * 0.13,
          Paint()..color = const Color(0xFF4A5A73),
        )
        ..drawCircle(ear, radius * 0.06, Paint()..color = visor);
    }
  }

  void _paintVisor(Canvas canvas, Offset center, double radius, Color visor) {
    final visorCenter = Offset(center.dx, center.dy - radius * 0.2);
    final visorRect = Rect.fromCenter(
      center: visorCenter,
      width: radius * 1.14,
      height: radius * 0.48,
    );
    final visorRRect = RRect.fromRectAndRadius(
      visorRect,
      Radius.circular(radius * 0.24),
    );
    canvas
      ..drawRRect(visorRRect, Paint()..color = const Color(0xFF101623))
      ..drawRRect(
        visorRRect,
        Paint()
          ..color = visor.withValues(alpha: 0.5)
          ..style = PaintingStyle.stroke
          ..strokeWidth = radius * 0.025,
      );

    // Thinking eyes drift sideways; everything else looks straight ahead.
    final sweep = thinkingDots ? math.sin(hover * 2 * math.pi) * 0.5 : 0.0;
    final gaze = (params.gazeDX + sweep).clamp(-1.0, 1.0);
    final eyeHeight =
        radius * 0.2 * params.eyeSize * params.eyeOpen * (1 - blink * 0.92);
    for (final side in [-1.0, 1.0]) {
      final eyeCenter = Offset(
        visorCenter.dx + side * radius * 0.28 + gaze * radius * 0.1,
        visorCenter.dy,
      );
      if (eyeHeight < radius * 0.02) {
        // Closed lids read as a glowing slit.
        canvas.drawLine(
          eyeCenter.translate(-radius * 0.09, 0),
          eyeCenter.translate(radius * 0.09, 0),
          Paint()
            ..color = visor
            ..strokeWidth = radius * 0.035
            ..strokeCap = StrokeCap.round,
        );
        continue;
      }
      canvas.drawOval(
        Rect.fromCenter(
          center: eyeCenter,
          width: radius * 0.2 * params.eyeSize,
          height: eyeHeight,
        ),
        Paint()..color = visor,
      );
      if (blink < 0.5) {
        canvas.drawCircle(
          eyeCenter.translate(-radius * 0.03, -eyeHeight * 0.2),
          radius * 0.035,
          Paint()..color = Colors.white.withValues(alpha: 0.9),
        );
      }
      if (params.browTilt.abs() > 0.05) {
        // Positive tilt angles the inner ends down: stern, not sad.
        final tilt = params.browTilt * side * -0.5;
        final browCenter = Offset(eyeCenter.dx, eyeCenter.dy - radius * 0.2);
        canvas.drawLine(
          browCenter +
              Offset(
                -math.cos(tilt) * radius * 0.1,
                -math.sin(tilt) * radius * 0.1,
              ),
          browCenter +
              Offset(
                math.cos(tilt) * radius * 0.1,
                math.sin(tilt) * radius * 0.1,
              ),
          Paint()
            ..color = const Color(0xFF4A5A73)
            ..strokeWidth = radius * 0.045
            ..strokeCap = StrokeCap.round,
        );
      }
    }
  }

  void _paintCheeks(Canvas canvas, Offset center, double radius, Color visor) {
    if (params.cheekGlow < 0.05) return;
    final cheek = Paint()
      ..color = visor.withValues(alpha: 0.8 * params.cheekGlow);
    for (final side in [-1.0, 1.0]) {
      canvas.drawCircle(
        Offset(center.dx + side * radius * 0.52, center.dy + radius * 0.3),
        radius * 0.05,
        cheek,
      );
    }
  }

  void _paintMouth(Canvas canvas, Offset center, double radius, Color visor) {
    final mouthCenter = Offset(center.dx, center.dy + radius * 0.33);
    final mouthRect = Rect.fromCenter(
      center: mouthCenter,
      width: radius * 0.68,
      height: radius * 0.26,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(mouthRect, Radius.circular(radius * 0.1)),
      Paint()..color = const Color(0xFF101623),
    );
    if (params.mouthActivity > 0.05) {
      for (var bar = 0; bar < 5; bar++) {
        final wave =
            (0.3 +
                    0.7 *
                        (0.5 +
                            0.5 *
                                math.sin(mouthFlap * math.pi * 2 + bar * 0.9)))
                .clamp(0.0, 1.0);
        final barHeight = mouthRect.height * 0.75 * wave * params.mouthActivity;
        canvas.drawRRect(
          RRect.fromRectAndRadius(
            Rect.fromCenter(
              center: Offset(
                mouthCenter.dx + (bar - 2) * radius * 0.11,
                mouthCenter.dy,
              ),
              width: radius * 0.06,
              height: math.max(barHeight, radius * 0.03),
            ),
            Radius.circular(radius * 0.03),
          ),
          Paint()..color = visor,
        );
      }
      return;
    }
    if (thinkingDots) {
      for (var dot = 0; dot < 3; dot++) {
        final alpha =
            0.35 + 0.65 * (0.5 + 0.5 * math.sin(hover * 2 * math.pi + dot));
        canvas.drawCircle(
          Offset(mouthCenter.dx + (dot - 1) * radius * 0.14, mouthCenter.dy),
          radius * 0.035,
          Paint()..color = visor.withValues(alpha: alpha),
        );
      }
      return;
    }
    final path = Path()
      ..moveTo(mouthCenter.dx - radius * 0.18, mouthCenter.dy)
      ..quadraticBezierTo(
        mouthCenter.dx,
        mouthCenter.dy + params.smile * radius * 0.2,
        mouthCenter.dx + radius * 0.18,
        mouthCenter.dy,
      );
    canvas.drawPath(
      path,
      Paint()
        ..color = visor.withValues(alpha: 0.9)
        ..style = PaintingStyle.stroke
        ..strokeWidth = radius * 0.045
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(_SadoFacePainter old) =>
      old.params.eyeOpen != params.eyeOpen ||
      old.params.eyeSize != params.eyeSize ||
      old.params.gazeDX != params.gazeDX ||
      old.params.mouthActivity != params.mouthActivity ||
      old.params.smile != params.smile ||
      old.params.browTilt != params.browTilt ||
      old.params.cheekGlow != params.cheekGlow ||
      old.params.visor != params.visor ||
      old.blink != blink ||
      old.hover != hover ||
      old.mouthFlap != mouthFlap ||
      old.thinkingDots != thinkingDots;
}
