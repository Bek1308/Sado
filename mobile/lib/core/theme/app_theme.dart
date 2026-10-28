import 'package:flutter/material.dart';
import 'package:sado/core/theme/app_spacing.dart';

abstract final class AppTheme {
  /// Meta blue, so Sado feels at home next to Meta's own products.
  static const _seedColor = Color(0xFF0064E0);

  /// Meta's lighter blue for dark backgrounds.
  static const _darkModeBlue = Color(0xFF2D88FF);

  /// Status green is not part of the seeded scheme, but "online" must read
  /// the same in light and dark mode.
  static const onlineColor = Color(0xFF34C759);

  /// Sado's own colours, shared with the launcher icon so the brand looks
  /// the same inside and outside the app.
  static const brandGradient = [
    Color(0xFF0082FB),
    Color(0xFF0064E0),
    Color(0xFF7A3FF2),
  ];

  static ThemeData get light => _build(Brightness.light);

  static ThemeData get dark => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final seeded = ColorScheme.fromSeed(
      seedColor: _seedColor,
      brightness: brightness,
      // Keeps the primary colour true to the seed instead of a muted tone.
      dynamicSchemeVariant: DynamicSchemeVariant.fidelity,
    );
    // Generated tones drift towards pastel; Meta's own blues stay saturated.
    final colors = seeded.copyWith(
      primary: brightness == Brightness.light ? _seedColor : _darkModeBlue,
      onPrimary: Colors.white,
    );
    final textTheme = ThemeData(colorScheme: colors).textTheme;

    return ThemeData(
      colorScheme: colors,
      scaffoldBackgroundColor: colors.surface,
      appBarTheme: AppBarTheme(
        backgroundColor: colors.surface,
        surfaceTintColor: Colors.transparent,
        scrolledUnderElevation: 0,
        titleTextStyle: textTheme.titleLarge?.copyWith(
          color: colors.onSurface,
          fontWeight: FontWeight.w600,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: colors.surfaceContainerHigh,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadius.lg),
          borderSide: BorderSide.none,
        ),
      ),
      chipTheme: ChipThemeData(
        // The filled colour already marks the choice; a tick would cover
        // the chip's emoji.
        showCheckmark: false,
        shape: const StadiumBorder(),
        side: BorderSide(color: colors.outlineVariant),
      ),
      popupMenuTheme: PopupMenuThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.md),
        ),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        showDragHandle: true,
        backgroundColor: colors.surfaceContainerLow,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(AppRadius.lg),
          ),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.sm),
        ),
      ),
    );
  }
}
