import 'package:flutter/material.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/conversation/presentation/widgets/sado_face.dart';
import 'package:sado/features/conversation/presentation/widgets/voice_wave.dart';

/// Sado's face and the live voice wave, always in view on a computer so a
/// glance tells whether it is listening, thinking or talking.
class DesktopStage extends StatelessWidget {
  const DesktopStage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.xl,
        AppSpacing.sm,
        AppSpacing.xl,
        AppSpacing.sm,
      ),
      child: Column(
        spacing: AppSpacing.md,
        children: [
          SadoFace(size: 110),
          VoiceWave(height: 44),
        ],
      ),
    );
  }
}
