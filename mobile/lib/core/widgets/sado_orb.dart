import 'package:flutter/material.dart';
import 'package:sado/core/theme/app_theme.dart';

/// Sado's mark: a warm orb carrying a sound wave.
class SadoOrb extends StatelessWidget {
  const SadoOrb({this.size = 40, this.glow = false, super.key});

  final double size;
  final bool glow;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: AppTheme.brandGradient,
        ),
        boxShadow: [
          if (glow)
            BoxShadow(
              color: AppTheme.brandGradient[1].withValues(alpha: 0.35),
              blurRadius: size / 3,
              spreadRadius: size / 12,
            ),
        ],
      ),
      child: Icon(
        Icons.graphic_eq,
        size: size / 2,
        color: Colors.white,
      ),
    );
  }
}
