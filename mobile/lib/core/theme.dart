import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// Espelham 1:1 as CSS custom properties de web/src/styles.css
// (:root[data-theme='dark'|'light']) — mudança de cor de marca precisa ser
// feita nos dois lugares.
abstract class AppColors {
  static const darkBg = Color(0xFF0B0E14);
  static const darkPanel = Color(0xFF161B25);
  static const darkPanel2 = Color(0xFF1B2230);
  static const darkText = Color(0xFFECEDEE);
  static const darkMuted = Color(0xFF9BA3B4);
  static const darkBorder = Color(0xFF232A36);
  static const darkAccent = Color(0xFF4ADE80);
  static const darkAccent2 = Color(0xFF22D3EE);
  static const darkWarn = Color(0xFFFBBF24);
  static const darkDanger = Color(0xFFF87171);

  static const lightBg = Color(0xFFF4F6FB);
  static const lightPanel = Color(0xFFFFFFFF);
  static const lightPanel2 = Color(0xFFF5F7FB);
  static const lightText = Color(0xFF1A202C);
  static const lightMuted = Color(0xFF4A5568);
  static const lightBorder = Color(0xFFD6DCE6);
  static const lightAccent = Color(0xFF16A34A);
  static const lightAccent2 = Color(0xFF0891B2);
  static const lightWarn = Color(0xFFD97706);
  static const lightDanger = Color(0xFFDC2626);
}

Color gainColor(Brightness b) => b == Brightness.dark ? AppColors.darkAccent : AppColors.lightAccent;

Color lossColor(Brightness b) => b == Brightness.dark ? AppColors.darkDanger : AppColors.lightDanger;

Color warnColor(Brightness b) => b == Brightness.dark ? AppColors.darkWarn : AppColors.lightWarn;

const double appRadius = 14;

ThemeData buildAppTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;
  final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
  final accent2 = isDark ? AppColors.darkAccent2 : AppColors.lightAccent2;
  final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
  final panel = isDark ? AppColors.darkPanel : AppColors.lightPanel;
  final text = isDark ? AppColors.darkText : AppColors.lightText;
  final muted = isDark ? AppColors.darkMuted : AppColors.lightMuted;
  final border = isDark ? AppColors.darkBorder : AppColors.lightBorder;
  final danger = isDark ? AppColors.darkDanger : AppColors.lightDanger;
  final warn = isDark ? AppColors.darkWarn : AppColors.lightWarn;

  final colorScheme = ColorScheme(
    brightness: brightness,
    primary: accent,
    onPrimary: isDark ? const Color(0xFF06210F) : Colors.white,
    secondary: accent2,
    onSecondary: isDark ? const Color(0xFF062125) : Colors.white,
    error: danger,
    onError: Colors.white,
    surface: panel,
    onSurface: text,
    tertiary: warn,
    onTertiary: isDark ? const Color(0xFF2B1D02) : Colors.white,
    outline: border,
  );

  final textTheme = GoogleFonts.interTextTheme(
    isDark ? ThemeData.dark().textTheme : ThemeData.light().textTheme,
  ).apply(bodyColor: text, displayColor: text);

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: bg,
    canvasColor: bg,
    fontFamily: GoogleFonts.inter().fontFamily,
    textTheme: textTheme,
    cardTheme: CardThemeData(
      color: panel,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(appRadius),
        side: BorderSide(color: border),
      ),
      margin: EdgeInsets.zero,
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: bg,
      foregroundColor: text,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: panel,
      indicatorColor: accent.withValues(alpha: 0.18),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 12,
          fontWeight: states.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w400,
          color: states.contains(WidgetState.selected) ? accent : muted,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected) ? accent : muted,
        ),
      ),
    ),
    dividerTheme: DividerThemeData(color: border, space: 1),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: isDark ? AppColors.darkPanel2 : AppColors.lightPanel2,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(appRadius),
        borderSide: BorderSide(color: border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(appRadius),
        borderSide: BorderSide(color: border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(appRadius),
        borderSide: BorderSide(color: accent, width: 1.5),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: panel,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(appRadius)),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: accent,
        foregroundColor: isDark ? const Color(0xFF06210F) : Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(appRadius)),
      ),
    ),
  );
}
