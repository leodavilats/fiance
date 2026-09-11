// A fundacao visual do produto, escrita a mao e sem gerador. E a unica paleta que existe:
// `test/contraste_test.dart` cobra o minimo da WCAG, e `tool/build_icons.py` le daqui a cor
// da marca.

import 'package:flutter/material.dart';

import 'product_rules.dart';

export 'product_rules.dart';

abstract final class FiColors {
  static const darkGround0 = Color(0xFF090C10);
  static const darkGround1 = Color(0xFF161C23);
  static const darkGround2 = Color(0xFF1F262F);
  static const darkHairline = Color(0xFF2F3945);
  static const darkHairlineStrong = Color(0xFF424E5C);
  static const darkControlBorder = Color(0xFF5A6B77);
  static const darkControlBorderHover = Color(0xFF738796);
  static const darkControlFill = Color(0xFF161C23);
  static const darkControlFillHover = Color(0xFF1F262F);
  static const darkControlFillActive = Color(0xFF2B3440);
  static const darkTrack = Color(0xFF252D38);
  static const darkInk1 = Color(0xFFE8EAEE);
  static const darkInk2 = Color(0xFFBABFC9);
  static const darkInk3 = Color(0xFFA0A6B1);
  static const darkInkDisabled = Color(0xFF6E7684);
  static const darkInkOnBrand = Color(0xFF08131A);
  static const darkBrand = Color(0xFF74ACC9);
  static const darkBrandHover = Color(0xFF9CC6DC);
  static const darkBrandActive = Color(0xFFB5D6E6);
  static const darkBrandStrong = Color(0xFF9CC6DC);
  static const darkBrandLight = Color(0xFF9CC6DC);
  static const darkBrandQuiet = Color(0xFF1D3140);
  static const darkStateFavorable = Color(0xFF58B68C);
  static const darkStateAttention = Color(0xFFD9A23B);
  static const darkStateAdverse = Color(0xFFE29184);
  static const darkStateIndeterminate = Color(0xFFA1A6A5);
  static const darkStateFavorableSurface = Color(0xFF1D3229);
  static const darkStateAttentionSurface = Color(0xFF3A321B);
  static const darkStateAdverseSurface = Color(0xFF372C28);
  static const darkStateIndeterminateSurface = Color(0xFF2A2F2D);
  static const darkDirectionUp = Color(0xFF89AD9D);
  static const darkDirectionDown = Color(0xFFC19D95);
  static const darkSeries1 = Color(0xFF74ACC9);
  static const darkSeries2 = Color(0xFF58B68C);
  static const darkSeries3 = Color(0xFFD9A23B);
  static const darkSeries4 = Color(0xFFE29184);
  static const darkSeries5 = Color(0xFFA69DD0);
  static const darkSeries6 = Color(0xFF5AB0B0);
  static const darkSeries7 = Color(0xFFD58CB1);
  static const darkSeries8 = Color(0xFFD69361);
  static const darkSeries9 = Color(0xFF9AAD56);
  static const darkSeries10 = Color(0xFF87A2DD);
  static const darkSeries11 = Color(0xFFC198AB);
  static const darkSeriesOther = Color(0xFF9FA5A2);

  static const lightGround0 = Color(0xFFEDF2F5);
  static const lightGround1 = Color(0xFFFFFFFF);
  static const lightGround2 = Color(0xFFEFF3F5);
  static const lightHairline = Color(0xFFD7DEE4);
  static const lightHairlineStrong = Color(0xFFA9B9C5);
  static const lightControlBorder = Color(0xFF708B9F);
  static const lightControlBorderHover = Color(0xFF577082);
  static const lightControlFill = Color(0xFFFFFFFF);
  static const lightControlFillHover = Color(0xFFE3EAEF);
  static const lightControlFillActive = Color(0xFFD5DEE4);
  static const lightTrack = Color(0xFFDCE3E9);
  static const lightInk1 = Color(0xFF1F2933);
  static const lightInk2 = Color(0xFF414956);
  static const lightInk3 = Color(0xFF4B5764);
  static const lightInkDisabled = Color(0xFF8493A1);
  static const lightInkOnBrand = Color(0xFFFFFFFF);
  static const lightBrand = Color(0xFF295D7C);
  static const lightBrandHover = Color(0xFF1F465D);
  static const lightBrandActive = Color(0xFF17364A);
  static const lightBrandStrong = Color(0xFF1F465D);
  static const lightBrandLight = Color(0xFF3F7898);
  static const lightBrandQuiet = Color(0xFFDCE9F0);
  static const lightStateFavorable = Color(0xFF116446);
  static const lightStateAttention = Color(0xFF784F0E);
  static const lightStateAdverse = Color(0xFF973A2D);
  static const lightStateIndeterminate = Color(0xFF515A55);
  static const lightStateFavorableSurface = Color(0xFFD7E5E0);
  static const lightStateAttentionSurface = Color(0xFFE8E1D6);
  static const lightStateAdverseSurface = Color(0xFFEFE1E0);
  static const lightStateIndeterminateSurface = Color(0xFFE1E3E2);
  static const lightDirectionUp = Color(0xFF33614D);
  static const lightDirectionDown = Color(0xFF7A4D41);
  static const lightSeries1 = Color(0xFF295D7C);
  static const lightSeries2 = Color(0xFF116446);
  static const lightSeries3 = Color(0xFF784F0E);
  static const lightSeries4 = Color(0xFF973A2D);
  static const lightSeries5 = Color(0xFF5C51A0);
  static const lightSeries6 = Color(0xFF156766);
  static const lightSeries7 = Color(0xFF924168);
  static const lightSeries8 = Color(0xFF8B4E1B);
  static const lightSeries9 = Color(0xFF56641C);
  static const lightSeries10 = Color(0xFF3B5AA8);
  static const lightSeries11 = Color(0xFF7A4E62);
  static const lightSeriesOther = Color(0xFF595F5C);

  // Veu sob drawer e sheet. Tem alfa, e por isso fica fora da varredura de contraste.
  static const darkOverlay = Color(0xA8030508);
  static const lightOverlay = Color(0x66151E26);
}

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
}

const String fiFontSans = 'IBM Plex Sans';
const String fiFontSerif = 'Source Serif 4';
