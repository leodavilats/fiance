// A fundacao visual do produto, escrita a mao e sem gerador. E a unica paleta que existe:
// `test/contraste_test.dart` cobra o minimo da WCAG, e `tool/build_icons.py` le daqui a cor
// da marca.

import 'package:flutter/material.dart';

import 'product_rules.dart';

export 'product_rules.dart';

abstract final class FiColors {
  static const darkGround0 = Color(0xFF15171B);
  static const darkGround1 = Color(0xFF1D2026);
  static const darkGround2 = Color(0xFF262A31);
  static const darkHairline = Color(0xFF333841);
  static const darkHairlineStrong = Color(0xFF474D58);
  static const darkControlBorder = Color(0xFF6A727E);
  static const darkControlBorderHover = Color(0xFF838C99);
  static const darkControlFill = Color(0xFF1D2026);
  static const darkControlFillHover = Color(0xFF262A31);
  static const darkControlFillActive = Color(0xFF31363F);
  static const darkTrack = Color(0xFF2B3039);
  static const darkInk1 = Color(0xFFE9E7E1);
  static const darkInk2 = Color(0xFFBBB8B0);
  static const darkInk3 = Color(0xFFA2A099);
  static const darkInkDisabled = Color(0xFF767369);
  static const darkInkOnBrand = Color(0xFF0B1015);
  static const darkBrand = Color(0xFF7DB0CB);
  static const darkBrandHover = Color(0xFF9EC8DE);
  static const darkBrandActive = Color(0xFFB6D7E7);
  static const darkBrandStrong = Color(0xFF9EC8DE);
  static const darkBrandLight = Color(0xFF9EC8DE);
  static const darkBrandQuiet = Color(0xFF1C3240);
  static const darkStateFavorable = Color(0xFF5CB98E);
  static const darkStateAttention = Color(0xFFDCA63F);
  static const darkStateAdverse = Color(0xFFE39588);
  static const darkStateIndeterminate = Color(0xFFA5A9A6);
  static const darkStateFavorableSurface = Color(0xFF1C3126);
  static const darkStateAttentionSurface = Color(0xFF3C351D);
  static const darkStateAdverseSurface = Color(0xFF3A2E2A);
  static const darkStateIndeterminateSurface = Color(0xFF2C312F);
  static const darkDirectionUp = Color(0xFF8CB0A0);
  static const darkDirectionDown = Color(0xFFC4A199);
  static const darkSeries1 = Color(0xFF7DB0CB);
  static const darkSeries2 = Color(0xFF5CB98E);
  static const darkSeries3 = Color(0xFFDCA63F);
  static const darkSeries4 = Color(0xFFE39588);
  static const darkSeries5 = Color(0xFFA9A1D3);
  static const darkSeries6 = Color(0xFF5FB4B4);
  static const darkSeries7 = Color(0xFFD892B5);
  static const darkSeries8 = Color(0xFFD99766);
  static const darkSeries9 = Color(0xFF9EB15B);
  static const darkSeries10 = Color(0xFF8CA6E0);
  static const darkSeries11 = Color(0xFFC59DAF);
  static const darkSeriesOther = Color(0xFFA3A9A6);

  static const lightGround0 = Color(0xFFF0EDE6);
  static const lightGround1 = Color(0xFFFAF8F3);
  static const lightGround2 = Color(0xFFE5E1D7);
  static const lightHairline = Color(0xFFD9D3C6);
  static const lightHairlineStrong = Color(0xFFADA593);
  static const lightControlBorder = Color(0xFF6D6655);
  static const lightControlBorderHover = Color(0xFF524C3E);
  static const lightControlFill = Color(0xFFFAF8F3);
  static const lightControlFillHover = Color(0xFFEDE9DF);
  static const lightControlFillActive = Color(0xFFDFDACD);
  static const lightTrack = Color(0xFFDED8CA);
  static const lightInk1 = Color(0xFF1C1B17);
  static const lightInk2 = Color(0xFF454238);
  static const lightInk3 = Color(0xFF5B574B);
  static const lightInkDisabled = Color(0xFF87816F);
  static const lightInkOnBrand = Color(0xFFF8F6F1);
  static const lightBrand = Color(0xFF1F5670);
  static const lightBrandHover = Color(0xFF164254);
  static const lightBrandActive = Color(0xFF0F3241);
  static const lightBrandStrong = Color(0xFF164254);
  static const lightBrandLight = Color(0xFF367191);
  static const lightBrandQuiet = Color(0xFFDDE6EA);
  static const lightStateFavorable = Color(0xFF0F5F41);
  static const lightStateAttention = Color(0xFF7A4B0C);
  static const lightStateAdverse = Color(0xFF97362A);
  static const lightStateIndeterminate = Color(0xFF4E4B42);
  static const lightStateFavorableSurface = Color(0xFFDEE7E1);
  static const lightStateAttentionSurface = Color(0xFFEDE4D3);
  static const lightStateAdverseSurface = Color(0xFFF0E2DE);
  static const lightStateIndeterminateSurface = Color(0xFFE6E3DB);
  static const lightDirectionUp = Color(0xFF3B5C4C);
  static const lightDirectionDown = Color(0xFF785047);
  static const lightSeries1 = Color(0xFF1F5670);
  static const lightSeries2 = Color(0xFF0F5F41);
  static const lightSeries3 = Color(0xFF7A4B0C);
  static const lightSeries4 = Color(0xFF97362A);
  static const lightSeries5 = Color(0xFF564C99);
  static const lightSeries6 = Color(0xFF12615F);
  static const lightSeries7 = Color(0xFF8C3D62);
  static const lightSeries8 = Color(0xFF854917);
  static const lightSeries9 = Color(0xFF525F18);
  static const lightSeries10 = Color(0xFF37549F);
  static const lightSeries11 = Color(0xFF75495D);
  static const lightSeriesOther = Color(0xFF55594F);

  // Veu sob drawer e sheet. Tem alfa, e por isso fica fora da varredura de contraste.
  static const darkOverlay = Color(0xA805070A);
  static const lightOverlay = Color(0x661E1B14);
}

Color fiGround0(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkGround0 : FiColors.lightGround0;

Color fiGround1(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkGround1 : FiColors.lightGround1;

Color fiGround2(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkGround2 : FiColors.lightGround2;

Color fiHairline(Brightness brightness) =>
    brightness == Brightness.dark ? FiColors.darkHairline : FiColors.lightHairline;

Color fiStateColor(FiState state, Brightness brightness) {
  final dark = brightness == Brightness.dark;
  switch (state) {
    case FiState.favorable:
      return dark ? FiColors.darkStateFavorable : FiColors.lightStateFavorable;
    case FiState.attention:
      return dark ? FiColors.darkStateAttention : FiColors.lightStateAttention;
    case FiState.adverse:
      return dark ? FiColors.darkStateAdverse : FiColors.lightStateAdverse;
    case FiState.indeterminate:
      return dark ? FiColors.darkStateIndeterminate : FiColors.lightStateIndeterminate;
    case FiState.neutral:
      return dark ? FiColors.darkInk2 : FiColors.lightInk2;
  }
}

Color fiStateSurface(FiState state, Brightness brightness) {
  final dark = brightness == Brightness.dark;
  switch (state) {
    case FiState.favorable:
      return dark ? FiColors.darkStateFavorableSurface : FiColors.lightStateFavorableSurface;
    case FiState.attention:
      return dark ? FiColors.darkStateAttentionSurface : FiColors.lightStateAttentionSurface;
    case FiState.adverse:
      return dark ? FiColors.darkStateAdverseSurface : FiColors.lightStateAdverseSurface;
    case FiState.indeterminate:
      return dark ? FiColors.darkStateIndeterminateSurface : FiColors.lightStateIndeterminateSurface;
    case FiState.neutral:
      return dark ? FiColors.darkGround2 : FiColors.lightGround2;
  }
}

Color fiDirectionColor(double delta, Brightness brightness) {
  final dark = brightness == Brightness.dark;
  if (delta > 0) return dark ? FiColors.darkDirectionUp : FiColors.lightDirectionUp;
  if (delta < 0) return dark ? FiColors.darkDirectionDown : FiColors.lightDirectionDown;
  return dark ? FiColors.darkInk2 : FiColors.lightInk2;
}

Color fiSeriesColor(int index, Brightness brightness) {
  final dark = brightness == Brightness.dark;
  switch (index) {
    case 1:
      return dark ? FiColors.darkSeries1 : FiColors.lightSeries1;
    case 2:
      return dark ? FiColors.darkSeries2 : FiColors.lightSeries2;
    case 3:
      return dark ? FiColors.darkSeries3 : FiColors.lightSeries3;
    case 4:
      return dark ? FiColors.darkSeries4 : FiColors.lightSeries4;
    case 5:
      return dark ? FiColors.darkSeries5 : FiColors.lightSeries5;
    case 6:
      return dark ? FiColors.darkSeries6 : FiColors.lightSeries6;
    case 7:
      return dark ? FiColors.darkSeries7 : FiColors.lightSeries7;
    case 8:
      return dark ? FiColors.darkSeries8 : FiColors.lightSeries8;
    case 9:
      return dark ? FiColors.darkSeries9 : FiColors.lightSeries9;
    case 10:
      return dark ? FiColors.darkSeries10 : FiColors.lightSeries10;
    case 11:
      return dark ? FiColors.darkSeries11 : FiColors.lightSeries11;
    default:
      return dark ? FiColors.darkSeriesOther : FiColors.lightSeriesOther;
  }
}

abstract final class FiSpace {
  static const s0 = 0.0;
  static const s1 = 4.0;
  static const s2 = 8.0;
  static const s3 = 12.0;
  static const s4 = 16.0;
  static const s5 = 20.0;
  static const s6 = 24.0;
  static const s8 = 32.0;
  static const s10 = 40.0;
  static const s12 = 48.0;
  static const s16 = 64.0;
}

abstract final class FiRadius {
  // Mais retos que antes (era 4/8/12): canto muito arredondado e o que faz uma tela de dinheiro
  // parecer aplicativo de banco.
  static const sm = 2.0;
  static const md = 6.0;
  static const lg = 10.0;
  static const pill = 999.0;
}

abstract final class FiLayout {
  // 44 e norma de acessibilidade, nao aparencia -- e o unico numero de layout que atravessa.
  static const minTouchTarget = 44.0;

  static const gutter = FiSpace.s4;
  static const scrollTail = FiSpace.s16;
}

abstract final class FiMotion {
  static const fast = Duration(milliseconds: 120);
  static const base = Duration(milliseconds: 180);
  static const slow = Duration(milliseconds: 240);
  static const easeEnter = Cubic(0.2, 0, 0, 1);
  static const easeExit = Cubic(0.4, 0, 1, 1);
}

abstract final class FiType {
  // Os mesmos PAPEIS do web, com valores de telefone. O topo do web (40, 30) nao cabe em 360dp,
  // e por isso nunca era usado; `caption` virava o corpo por falta de alternativa.
  static const moneyXl = TextStyle(
    fontSize: 32,
    height: 1.125,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.8,
    fontFeatures: [FontFeature.tabularFigures(), FontFeature.slashedZero()],
  );
  static const moneyLg = TextStyle(
    fontSize: 26,
    height: 1.154,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.52,
    fontFeatures: [FontFeature.tabularFigures(), FontFeature.slashedZero()],
  );
  static const metric = TextStyle(
    fontSize: 20,
    height: 1.3,
    fontWeight: FontWeight.w600,
    fontFeatures: [FontFeature.tabularFigures(), FontFeature.slashedZero()],
  );
  static const metricSm = TextStyle(
    fontSize: 16,
    height: 1.375,
    fontWeight: FontWeight.w600,
    fontFeatures: [FontFeature.tabularFigures(), FontFeature.slashedZero()],
  );
  static const verdict = TextStyle(
    fontSize: 19,
    height: 1.474,
    fontWeight: FontWeight.w400,
  );
  static const verdictSm = TextStyle(
    fontSize: 16,
    height: 1.5,
    fontWeight: FontWeight.w400,
  );
  static const pageTitle = TextStyle(
    fontSize: 22,
    height: 1.273,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.44,
  );
  static const title = TextStyle(
    fontSize: 16,
    height: 1.375,
    fontWeight: FontWeight.w600,
  );
  static const eyebrow = TextStyle(
    fontSize: 11,
    height: 1.364,
    fontWeight: FontWeight.w600,
    letterSpacing: 1.1,
  );
  // 16, e nao 15: em 360dp o corpo precisa de corpo, e era por isso que 44 usos de `caption`
  // faziam o papel dele.
  static const body = TextStyle(
    fontSize: 16,
    height: 1.5,
    fontWeight: FontWeight.w400,
  );
  static const bodyLg = TextStyle(
    fontSize: 18,
    height: 1.556,
    fontWeight: FontWeight.w400,
  );
  static const label = TextStyle(
    fontSize: 14,
    height: 1.429,
    fontWeight: FontWeight.w500,
  );
  static const caption = TextStyle(
    fontSize: 13,
    height: 1.385,
    fontWeight: FontWeight.w400,
  );
  static const ticker = TextStyle(
    fontSize: 14,
    height: 1.286,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.7,
    fontFeatures: [FontFeature.tabularFigures(), FontFeature.slashedZero()],
  );
  static const figure = TextStyle(
    fontSize: 15,
    height: 1.4,
    fontWeight: FontWeight.w500,
    fontFeatures: [FontFeature.tabularFigures(), FontFeature.slashedZero()],
  );
  static const axis = TextStyle(
    fontSize: 11,
    height: 1.273,
    fontWeight: FontWeight.w400,
    fontFeatures: [FontFeature.tabularFigures(), FontFeature.slashedZero()],
  );
  static const action = TextStyle(
    fontSize: 15,
    height: 1.2,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.1,
  );
}

const String fiFontSans = 'IBM Plex Sans';
const String fiFontSerif = 'Source Serif 4';
