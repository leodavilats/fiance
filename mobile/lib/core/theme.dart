import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'design_tokens.dart';

export 'design_tokens.dart';

Color fiInk1(BuildContext context) => fiInk1Of(Theme.of(context).brightness);

Color fiInk1Of(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkInk1 : FiColors.lightInk1;

Color fiInk2(BuildContext context) => fiInk2Of(Theme.of(context).brightness);

Color fiInk2Of(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkInk2 : FiColors.lightInk2;

Color fiInk3(BuildContext context) => fiInk3Of(Theme.of(context).brightness);

Color fiInk3Of(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkInk3 : FiColors.lightInk3;

const double appRadius = FiRadius.md;

TextStyle fiSerif(TextStyle base) => GoogleFonts.sourceSerif4(textStyle: base);

TextStyle fiSans(TextStyle base) => GoogleFonts.ibmPlexSans(textStyle: base);

ThemeData buildAppTheme(Brightness brightness) {
  final isDark = brightness == Brightness.dark;

  final ground0 = isDark ? FiColors.darkGround0 : FiColors.lightGround0;
  final ground1 = isDark ? FiColors.darkGround1 : FiColors.lightGround1;
  final ground2 = isDark ? FiColors.darkGround2 : FiColors.lightGround2;
  final hairline = isDark ? FiColors.darkHairline : FiColors.lightHairline;
  final hairlineStrong = isDark ? FiColors.darkHairlineStrong : FiColors.lightHairlineStrong;
  final controlBorder = isDark ? FiColors.darkControlBorder : FiColors.lightControlBorder;
  final controlFill = isDark ? FiColors.darkControlFill : FiColors.lightControlFill;
  final controlFillHover = isDark
      ? FiColors.darkControlFillHover
      : FiColors.lightControlFillHover;
  final track = isDark ? FiColors.darkTrack : FiColors.lightTrack;
  final inkDisabled = isDark ? FiColors.darkInkDisabled : FiColors.lightInkDisabled;
  final ink1 = isDark ? FiColors.darkInk1 : FiColors.lightInk1;
  final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;
  final ink3 = fiInk3Of(brightness);
  final brand = isDark ? FiColors.darkBrand : FiColors.lightBrand;
  final brandQuiet = isDark ? FiColors.darkBrandQuiet : FiColors.lightBrandQuiet;
  final inkOnBrand = isDark ? FiColors.darkInkOnBrand : FiColors.lightInkOnBrand;
  final favorable = fiStateColor(FiState.favorable, brightness);
  final attention = fiStateColor(FiState.attention, brightness);
  final adverse = fiStateColor(FiState.adverse, brightness);

  final colorScheme = ColorScheme(
    brightness: brightness,
    primary: brand,
    onPrimary: inkOnBrand,
    primaryContainer: brandQuiet,
    onPrimaryContainer: ink1,
    secondary: favorable,
    onSecondary: inkOnBrand,
    error: adverse,
    onError: isDark ? FiColors.darkInk1 : FiColors.lightGround1,
    surface: ground1,
    onSurface: ink1,
    onSurfaceVariant: ink2,
    surfaceContainerLowest: ground0,
    surfaceContainerLow: ground0,
    surfaceContainer: ground1,
    surfaceContainerHigh: ground2,
    surfaceContainerHighest: ground2,
    tertiary: attention,
    onTertiary: isDark ? FiColors.darkInk1 : FiColors.lightGround1,
    outline: hairline,
    outlineVariant: hairlineStrong,
    shadow: isDark ? FiColors.darkOverlay : FiColors.lightOverlay,
  );

  final baseTextTheme = isDark ? ThemeData.dark().textTheme : ThemeData.light().textTheme;
  final textTheme = GoogleFonts.ibmPlexSansTextTheme(
    baseTextTheme,
  ).apply(bodyColor: ink1, displayColor: ink1);

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: ground0,
    canvasColor: ground0,
    fontFamily: GoogleFonts.ibmPlexSans().fontFamily,
    textTheme: textTheme,
    splashFactory: InkSparkle.splashFactory,
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
      scrolledUnderElevation: 0,
      surfaceTintColor: Colors.transparent,
      centerTitle: false,
      titleSpacing: FiLayout.gutter,
      titleTextStyle: GoogleFonts.ibmPlexSans(textStyle: FiType.pageTitle).copyWith(color: ink1),
      iconTheme: IconThemeData(color: ink2, size: 22),
      actionsIconTheme: IconThemeData(color: ink2, size: 22),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: ground1,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      height: 64,
      indicatorColor: Colors.transparent,
      indicatorShape: const RoundedRectangleBorder(),
      labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => GoogleFonts.ibmPlexSans(
          textStyle: TextStyle(
            fontSize: 11,
            height: 1.3,
            letterSpacing: 0.2,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w600
                : FontWeight.w400,
            color: states.contains(WidgetState.selected) ? ink1 : ink3,
          ),
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          size: 22,
          color: states.contains(WidgetState.selected) ? ink1 : ink3,
        ),
      ),
    ),
    dividerTheme: DividerThemeData(color: hairline, space: 1, thickness: 1),
    iconTheme: IconThemeData(color: ink2, size: 20),
    listTileTheme: ListTileThemeData(
      textColor: ink1,
      iconColor: ink2,
      titleTextStyle: FiType.body.copyWith(color: ink1),
      subtitleTextStyle: FiType.caption.copyWith(color: ink2),
      minVerticalPadding: FiSpace.s2,
      shape: const RoundedRectangleBorder(),
    ),
    // Contorno de campo e `controlBorder`, nao `hairline`: com o token de separador a borda
    // desenhava a 1,20:1 no tema claro, contra os 3:1 que a WCAG 1.4.11 pede de um controle.
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: controlFill,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: FiSpace.s3,
        vertical: FiSpace.s3,
      ),
      labelStyle: FiType.label.copyWith(color: ink2),
      floatingLabelStyle: FiType.caption.copyWith(color: ink2),
      helperStyle: FiType.caption.copyWith(color: ink3),
      hintStyle: FiType.body.copyWith(color: ink3),
      errorStyle: FiType.caption.copyWith(color: adverse),
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
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: adverse),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: adverse, width: 1.5),
      ),
      disabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        borderSide: BorderSide(color: hairlineStrong),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: ground1,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      titleTextStyle: fiSerif(FiType.verdictSm).copyWith(color: ink1),
      contentTextStyle: FiType.body.copyWith(color: ink2),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(FiRadius.lg),
        side: BorderSide(color: hairline),
      ),
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: ground1,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      modalBarrierColor: isDark ? FiColors.darkOverlay : FiColors.lightOverlay,
      dragHandleColor: hairlineStrong,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(FiRadius.lg)),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: isDark ? FiColors.darkGround2 : FiColors.lightInk1,
      contentTextStyle: FiType.body.copyWith(
        color: isDark ? FiColors.darkInk1 : FiColors.lightGround1,
      ),
      actionTextColor: isDark ? FiColors.darkBrand : FiColors.lightBrandLight,
      behavior: SnackBarBehavior.floating,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
    ),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: brand,
      foregroundColor: inkOnBrand,
      elevation: 2,
      focusElevation: 2,
      hoverElevation: 2,
      highlightElevation: 2,
      extendedTextStyle: FiType.action,
      extendedPadding: const EdgeInsets.symmetric(horizontal: FiSpace.s5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: brand,
        foregroundColor: inkOnBrand,
        disabledBackgroundColor: controlFillHover,
        disabledForegroundColor: inkDisabled,
        textStyle: FiType.action,
        minimumSize: const Size(0, FiLayout.minTouchTarget),
        padding: const EdgeInsets.symmetric(horizontal: FiSpace.s5),
        elevation: 0,
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
        textStyle: FiType.action,
        minimumSize: const Size(0, FiLayout.minTouchTarget),
        padding: const EdgeInsets.symmetric(horizontal: FiSpace.s4),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: brand,
        disabledForegroundColor: inkDisabled,
        textStyle: FiType.action,
        minimumSize: const Size(0, FiLayout.minTouchTarget),
        padding: const EdgeInsets.symmetric(horizontal: FiSpace.s2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.sm)),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(
        foregroundColor: ink2,
        minimumSize: const Size(FiLayout.minTouchTarget, FiLayout.minTouchTarget),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
      ),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        textStyle: WidgetStatePropertyAll(FiType.label),
        side: WidgetStatePropertyAll(BorderSide(color: controlBorder)),
        backgroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? brandQuiet : controlFill,
        ),
        foregroundColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected) ? ink1 : ink2,
        ),
        visualDensity: VisualDensity.compact,
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
        ),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: controlFill,
      selectedColor: brandQuiet,
      disabledColor: ground2,
      side: BorderSide(color: controlBorder),
      labelStyle: FiType.label.copyWith(color: ink1),
      secondaryLabelStyle: FiType.label.copyWith(color: ink1),
      checkmarkColor: ink1,
      showCheckmark: false,
      padding: const EdgeInsets.symmetric(horizontal: FiSpace.s2, vertical: FiSpace.s1),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.md)),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected) ? inkOnBrand : controlFill,
      ),
      trackColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected) ? brand : track,
      ),
      trackOutlineColor: WidgetStatePropertyAll(controlBorder),
    ),
    checkboxTheme: CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected) ? brand : Colors.transparent,
      ),
      checkColor: WidgetStatePropertyAll(inkOnBrand),
      side: BorderSide(color: controlBorder, width: 1.5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(FiRadius.sm)),
    ),
    radioTheme: RadioThemeData(
      fillColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected) ? brand : controlBorder,
      ),
    ),
    progressIndicatorTheme: ProgressIndicatorThemeData(
      color: brand,
      linearTrackColor: track,
      circularTrackColor: track,
      linearMinHeight: 6,
    ),
    expansionTileTheme: ExpansionTileThemeData(
      iconColor: ink3,
      collapsedIconColor: ink3,
      textColor: ink1,
      collapsedTextColor: ink1,
      shape: const Border(),
      collapsedShape: const Border(),
      tilePadding: EdgeInsets.zero,
    ),
    tooltipTheme: TooltipThemeData(
      decoration: BoxDecoration(
        color: isDark ? FiColors.darkGround2 : FiColors.lightInk1,
        borderRadius: BorderRadius.circular(FiRadius.sm),
      ),
      textStyle: FiType.caption.copyWith(
        color: isDark ? FiColors.darkInk1 : FiColors.lightGround1,
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
      valueIndicatorColor: isDark ? FiColors.darkGround2 : FiColors.lightInk1,
      valueIndicatorTextStyle: FiType.caption.copyWith(
        color: isDark ? FiColors.darkInk1 : FiColors.lightGround1,
      ),
    ),
    focusColor: brand.withValues(alpha: 0.16),
    highlightColor: brand.withValues(alpha: 0.08),
    splashColor: brand.withValues(alpha: 0.10),
  );
}
