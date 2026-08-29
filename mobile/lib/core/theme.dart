import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'design_tokens.dart';

export 'design_tokens.dart';

abstract final class AppColors {
  static const darkBg = FiColors.darkGround0;
  static const darkPanel = FiColors.darkGround1;
  static const darkPanel2 = FiColors.darkGround2;
  static const darkText = FiColors.darkInk1;
  static const darkMuted = FiColors.darkInk2;
  static const darkBorder = FiColors.darkHairline;
  static const darkAccent = FiColors.darkBrand;
  static const darkAccent2 = FiColors.darkBrand;
  static const darkWarn = FiColors.darkStateAttention;
  static const darkDanger = FiColors.darkStateAdverse;

  static const lightBg = FiColors.lightGround0;
  static const lightPanel = FiColors.lightGround1;
  static const lightPanel2 = FiColors.lightGround2;
  static const lightText = FiColors.lightInk1;
  static const lightMuted = FiColors.lightInk2;
  static const lightBorder = FiColors.lightHairline;
  static const lightAccent = FiColors.lightBrand;
  static const lightAccent2 = FiColors.lightBrand;
  static const lightWarn = FiColors.lightStateAttention;
  static const lightDanger = FiColors.lightStateAdverse;
}

/// Tinta secundaria e terciaria pelo tema corrente.
///
/// Existem porque o codigo usava `Colors.grey.shade600` em ~40 lugares: cinza
/// fixo e o mesmo em claro e escuro, entao o rotulo que fica legivel de dia
/// some a noite. Estes dois leem o tema e saem dos tokens.
Color fiInk2(BuildContext context) =>
    Theme.of(context).brightness == Brightness.dark ? FiColors.darkInk2 : FiColors.lightInk2;

Color fiInk3(BuildContext context) =>
    Theme.of(context).brightness == Brightness.dark ? FiColors.darkInk3 : FiColors.lightInk3;

const double appRadius = FiRadius.md;

TextStyle fiSerif(TextStyle base) => GoogleFonts.sourceSerif4(textStyle: base);

TextStyle fiSans(TextStyle base) => GoogleFonts.inter(textStyle: base);

ThemeData buildAppTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;

  final ground0 = isDark ? FiColors.darkGround0 : FiColors.lightGround0;
  final ground1 = isDark ? FiColors.darkGround1 : FiColors.lightGround1;
  final ground2 = isDark ? FiColors.darkGround2 : FiColors.lightGround2;
  final hairline = isDark ? FiColors.darkHairline : FiColors.lightHairline;
  final ink1 = isDark ? FiColors.darkInk1 : FiColors.lightInk1;
  final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;
  final brand = isDark ? FiColors.darkBrand : FiColors.lightBrand;
  final inkOnBrand = isDark ? FiColors.darkInkOnBrand : FiColors.lightInkOnBrand;
  final favorable = fiStateColor(FiState.favorable, brightness);
  final attention = fiStateColor(FiState.attention, brightness);
  final adverse = fiStateColor(FiState.adverse, brightness);

  final colorScheme = ColorScheme(
    brightness: brightness,
    primary: brand,
    onPrimary: inkOnBrand,
    secondary: favorable,
    onSecondary: inkOnBrand,
    error: adverse,
    onError: isDark ? FiColors.darkInk1 : FiColors.lightGround1,
    surface: ground1,
    onSurface: ink1,
    surfaceContainerHighest: ground2,
    tertiary: attention,
    onTertiary: isDark ? FiColors.darkInk1 : FiColors.lightGround1,
    outline: hairline,
    outlineVariant: isDark ? FiColors.darkHairlineStrong : FiColors.lightHairlineStrong,
  );

  final baseTextTheme = isDark ? ThemeData.dark().textTheme : ThemeData.light().textTheme;
  final textTheme = GoogleFonts.interTextTheme(
    baseTextTheme,
  ).apply(bodyColor: ink1, displayColor: ink1);

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: ground0,
    canvasColor: ground0,
    fontFamily: GoogleFonts.inter().fontFamily,
    textTheme: textTheme,
    cardTheme: CardThemeData(
      color: ground1,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        side: BorderSide(color: hairline),
      ),
      margin: EdgeInsets.zero,
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: ground0,
      foregroundColor: ink1,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: ground1,
      indicatorColor: brand.withValues(alpha: 0.18),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 12,
          fontWeight: states.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w400,
          color: states.contains(WidgetState.selected) ? brand : ink2,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(color: states.contains(WidgetState.selected) ? brand : ink2),
      ),
    ),
    dividerTheme: DividerThemeData(color: hairline, space: 1),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: ground2,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: hairline),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: hairline),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: brand, width: 1.5),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: ground1,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.lg)),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: ground1,
      surfaceTintColor: Colors.transparent,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(FiRadius.lg)),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: brand,
        foregroundColor: inkOnBrand,
        minimumSize: const Size(0, FiLayout.minTouchTarget),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
      ),
    ),
    sliderTheme: SliderThemeData(
      activeTrackColor: brand,
      inactiveTrackColor: hairline,
      thumbColor: brand,
      overlayColor: brand.withValues(alpha: 0.12),
    ),
    focusColor: brand.withValues(alpha: 0.16),
  );
}
