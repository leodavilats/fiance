import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'design_tokens.dart';

export 'design_tokens.dart';

Color fiInk2(BuildContext context) =>
    Theme.of(context).brightness == Brightness.dark ? FiColors.darkInk2 : FiColors.lightInk2;

Color fiInk3(BuildContext context) => fiInk3Of(Theme.of(context).brightness);

Color fiInk3Of(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkInk3 : FiColors.lightInk3;

const double appRadius = FiRadius.md;

TextStyle fiSerif(TextStyle base) => GoogleFonts.sourceSerif4(textStyle: base);

TextStyle fiSans(TextStyle base) => GoogleFonts.inter(textStyle: base);

ThemeData buildAppTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;

  final ground0 = isDark ? FiColors.darkGround0 : FiColors.lightGround0;
  final ground1 = isDark ? FiColors.darkGround1 : FiColors.lightGround1;
  final ground2 = isDark ? FiColors.darkGround2 : FiColors.lightGround2;
  final hairline = isDark ? FiColors.darkHairline : FiColors.lightHairline;
  final hairlineStrong = isDark ? FiColors.darkHairlineStrong : FiColors.lightHairlineStrong;
  final controlBorder = isDark ? FiColors.darkControlBorder : FiColors.lightControlBorder;
  final controlFill = isDark ? FiColors.darkControlFill : FiColors.lightControlFill;
  final track = isDark ? FiColors.darkTrack : FiColors.lightTrack;
  final inkDisabled = isDark ? FiColors.darkInkDisabled : FiColors.lightInkDisabled;
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
      // 13px e o papel de rotulo; 12 e o de legenda. O web usa `fi-label` nas duas navegacoes,
      // e cinco destinos iguais nas duas plataformas valem tambem para o tipo.
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 13,
          fontWeight: states.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w400,
          color: states.contains(WidgetState.selected) ? brand : ink2,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(color: states.contains(WidgetState.selected) ? brand : ink2),
      ),
    ),
    dividerTheme: DividerThemeData(color: hairline, space: 1),
    // Contorno de campo e `controlBorder`, nao `hairline`: com o token de separador a borda
    // desenhava a 1,20:1 no tema claro, contra os 3:1 que a WCAG 1.4.11 pede de um controle.
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: controlFill,
      hintStyle: TextStyle(color: fiInk3Of(brightness)),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: controlBorder),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: controlBorder),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: brand, width: 1.5),
      ),
      disabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: hairlineStrong),
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
        disabledBackgroundColor: isDark
            ? FiColors.darkControlFillHover
            : FiColors.lightControlFillHover,
        disabledForegroundColor: inkDisabled,
        minimumSize: const Size(0, FiLayout.minTouchTarget),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
      ),
    ),

    // O botao secundario nao era declarado, e caia no padrao do Material -- outra grafia de
    // botao, com outra altura e outro contorno, ao lado do primario do sistema.
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        backgroundColor: controlFill,
        foregroundColor: ink1,
        disabledForegroundColor: inkDisabled,
        side: BorderSide(color: controlBorder),
        minimumSize: const Size(0, FiLayout.minTouchTarget),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: brand,
        disabledForegroundColor: inkDisabled,
        minimumSize: const Size(0, FiLayout.minTouchTarget),
      ),
    ),
    // Trilho vazio e o poco, e nao o separador: `brand` sobre `hairline` ficava a 2,28:1, e
    // era o par que faz um deslizador mostrar onde esta.
    sliderTheme: SliderThemeData(
      trackHeight: 8,
      activeTrackColor: brand,
      inactiveTrackColor: track,
      thumbColor: brand,
      disabledActiveTrackColor: hairlineStrong,
      disabledInactiveTrackColor: track,
      disabledThumbColor: hairlineStrong,
      overlayColor: brand.withValues(alpha: 0.12),
    ),
    focusColor: brand.withValues(alpha: 0.16),
  );
}
