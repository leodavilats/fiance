import 'package:flutter/material.dart';

abstract final class FiColors {
  static const darkGround0 = Color(0xFF090C10);
  static const darkGround1 = Color(0xFF161C23);
  static const darkGround2 = Color(0xFF1F262F);
  static const darkHairline = Color(0xFF2F3945);
  static const darkHairlineStrong = Color(0xFF424E5C);
  static const darkInk1 = Color(0xFFE8EAEE);
  static const darkInk2 = Color(0xFFBABFC9);
  static const darkInk3 = Color(0xFFA0A6B1);
  static const darkInkOnBrand = Color(0xFF08131A);
  static const darkBrand = Color(0xFF74ACC9);
  static const darkBrandStrong = Color(0xFF3F7898);
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

  static const lightGround0 = Color(0xFFF7F9FA);
  static const lightGround1 = Color(0xFFFFFFFF);
  static const lightGround2 = Color(0xFFEFF3F6);
  static const lightHairline = Color(0xFFD9E2E8);
  static const lightHairlineStrong = Color(0xFFB6C2CC);
  static const lightInk1 = Color(0xFF1F2933);
  static const lightInk2 = Color(0xFF414956);
  static const lightInk3 = Color(0xFF525B6C);
  static const lightInkOnBrand = Color(0xFFFFFFFF);
  static const lightBrand = Color(0xFF295D7C);
  static const lightBrandStrong = Color(0xFF1F465D);
  static const lightBrandLight = Color(0xFF3F7898);
  static const lightBrandQuiet = Color(0xFFEAF2F6);
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

}

enum FiState { favorable, attention, adverse, neutral, indeterminate }

Color fiStateColor(FiState state, Brightness brightness) {
  final dark = brightness == Brightness.dark;
  switch (state) {
    case FiState.favorable:
      return dark ? FiColors.darkStateFavorable : FiColors.lightStateFavorable;
    case FiState.attention:
      return dark ? FiColors.darkStateAttention : FiColors.lightStateAttention;
    case FiState.adverse:
      return dark ? FiColors.darkStateAdverse : FiColors.lightStateAdverse;
    case FiState.neutral:
      return dark ? FiColors.darkInk2 : FiColors.lightInk2;
    case FiState.indeterminate:
      return dark ? FiColors.darkStateIndeterminate : FiColors.lightStateIndeterminate;
  }
}

Color fiStateSurface(FiState state, Brightness brightness) {
  final dark = brightness == Brightness.dark;
  switch (state) {
    case FiState.favorable:
      return dark
          ? FiColors.darkStateFavorableSurface
          : FiColors.lightStateFavorableSurface;
    case FiState.attention:
      return dark
          ? FiColors.darkStateAttentionSurface
          : FiColors.lightStateAttentionSurface;
    case FiState.adverse:
      return dark
          ? FiColors.darkStateAdverseSurface
          : FiColors.lightStateAdverseSurface;
    case FiState.neutral:
      return dark ? FiColors.darkGround2 : FiColors.lightGround2;
    case FiState.indeterminate:
      return dark
          ? FiColors.darkStateIndeterminateSurface
          : FiColors.lightStateIndeterminateSurface;
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
  static const sm = 4.0;
  static const md = 8.0;
  static const lg = 12.0;
  static const pill = 999.0;
}

abstract final class FiMotion {
  static const fast = Duration(milliseconds: 120);
  static const base = Duration(milliseconds: 180);
  static const slow = Duration(milliseconds: 240);
  static const easeEnter = Cubic(0.2, 0, 0, 1);
  static const easeExit = Cubic(0.4, 0, 1, 1);
}

abstract final class FiBreakpoint {
  static const mobileSm = 0.0;
  static const mobileLg = 420.0;
  static const tablet = 768.0;
  static const desktopSm = 1024.0;
  static const desktop = 1280.0;
  static const desktopLg = 1440.0;
}

abstract final class FiLayout {
  static const readingMaxWidth = 1120.0;
  static const denseMaxWidth = 1600.0;
  static const drawerWidth = 600.0;
  static const subnavWidth = 200.0;
  static const navHeight = 56.0;
  static const minTouchTarget = 44.0;
}

enum FiDensity {
  comfortable(rowHeight: 48, sectionGap: 32, blockPadding: 20),
  compact(rowHeight: 36, sectionGap: 24, blockPadding: 14),
  ;

  const FiDensity({
    required this.rowHeight,
    required this.sectionGap,
    required this.blockPadding,
  });

  final double rowHeight;
  final double sectionGap;
  final double blockPadding;
}

abstract final class FiType {
  static const moneyXl = TextStyle(
    fontSize: 44,
    height: 1.091,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.88,
    fontFeatures: [
      FontFeature.tabularFigures(),
      FontFeature.slashedZero(),
    ],
  );
  static const moneyLg = TextStyle(
    fontSize: 32,
    height: 1.125,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.32,
    fontFeatures: [
      FontFeature.tabularFigures(),
      FontFeature.slashedZero(),
    ],
  );
  static const metric = TextStyle(
    fontSize: 22,
    height: 1.273,
    fontWeight: FontWeight.w600,
    fontFeatures: [
      FontFeature.tabularFigures(),
      FontFeature.slashedZero(),
    ],
  );
  static const metricSm = TextStyle(
    fontSize: 16,
    height: 1.375,
    fontWeight: FontWeight.w600,
    fontFeatures: [
      FontFeature.tabularFigures(),
      FontFeature.slashedZero(),
    ],
  );
  static const verdict = TextStyle(
    fontSize: 20,
    height: 1.400,
    fontWeight: FontWeight.w400,
  );
  static const verdictSm = TextStyle(
    fontSize: 16,
    height: 1.500,
    fontWeight: FontWeight.w400,
  );
  static const title = TextStyle(
    fontSize: 15,
    height: 1.333,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.15,
  );
  static const eyebrow = TextStyle(
    fontSize: 11,
    height: 1.273,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.88,
  );
  static const body = TextStyle(
    fontSize: 14,
    height: 1.500,
    fontWeight: FontWeight.w400,
  );
  static const label = TextStyle(
    fontSize: 13,
    height: 1.385,
    fontWeight: FontWeight.w500,
  );
  static const caption = TextStyle(
    fontSize: 12,
    height: 1.333,
    fontWeight: FontWeight.w400,
  );
  static const ticker = TextStyle(
    fontSize: 14,
    height: 1.286,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.56,
  );
}

const Map<String, String> fiTypeFamily = {
  'money-xl': 'sans',
  'money-lg': 'sans',
  'metric': 'sans',
  'metric-sm': 'sans',
  'verdict': 'serif',
  'verdict-sm': 'serif',
  'title': 'sans',
  'eyebrow': 'sans',
  'body': 'sans',
  'label': 'sans',
  'caption': 'sans',
  'ticker': 'sans',
};

const String fiFontSans = 'Inter';
const String fiFontSerif = 'Source Serif 4';

const double kScoreStrong = 75;
const double kScoreGood = 60;
const double kScoreNeutral = 40;
const double kMinDataCompleteness = 0.5;
const double kHighlightMinDy = 6;

class FiScoreBand {
  const FiScoreBand({
    required this.id,
    required this.min,
    required this.max,
    required this.label,
    required this.state,
    required this.emphasis,
  });

  final String id;
  final double? min;
  final double? max;
  final String label;
  final FiState state;
  final String emphasis;
}

const List<FiScoreBand> fiScoreBands = [
  FiScoreBand(id: 'strong', min: 75, max: 100, label: 'Forte', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'good', min: 60, max: 74, label: 'Boa', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'neutral', min: 40, max: 59, label: 'Neutra', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'weak', min: 0, max: 39, label: 'Fraca', state: FiState.adverse, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem dado', state: FiState.indeterminate, emphasis: 'muted'),
];

abstract final class FiScoreRulerSize {
  static const inline = 16.0;
  static const list = 24.0;
  static const card = 40.0;
  static const page = 64.0;
}

bool fiScoreIsReliable(double? dataCompleteness) =>
    (dataCompleteness ?? 1) >= kMinDataCompleteness;

FiScoreBand fiScoreBandFor(double score, double? dataCompleteness) {
  if (!fiScoreIsReliable(dataCompleteness)) {
    return fiScoreBands.firstWhere((b) => b.id == 'insufficient');
  }
  return fiScoreBands.firstWhere(
    (b) => b.min != null && score >= b.min!,
    orElse: () => fiScoreBands.firstWhere((b) => b.id == 'weak'),
  );
}

const List<FiScoreBand> fiHealthBands = [
  FiScoreBand(id: 'healthy', min: 75, max: 100, label: 'Saudável', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'ok', min: 60, max: 74, label: 'Em ordem', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'watch', min: 40, max: 59, label: 'Atenção', state: FiState.attention, emphasis: 'muted'),
  FiScoreBand(id: 'fragile', min: 0, max: 39, label: 'Frágil', state: FiState.adverse, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Carteira pequena demais para avaliar', state: FiState.indeterminate, emphasis: 'muted'),
];

const List<FiScoreBand> fiMarginOfSafetyBands = [
  FiScoreBand(id: 'wide', min: 25, max: 50, label: 'Desconto amplo', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'some', min: 10, max: 24, label: 'Algum desconto', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'fair', min: 0, max: 9, label: 'Perto do justo', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'above', min: -50, max: -1, label: 'Acima do justo', state: FiState.attention, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem preço justo', state: FiState.indeterminate, emphasis: 'muted'),
];

const ({double min, double max}) fiMarginOfSafetyDomain = (min: -50, max: 50);

const List<FiScoreBand> fiAllocationGapBands = [
  FiScoreBand(id: 'relevant', min: 5, max: 20, label: 'Desvio relevante', state: FiState.attention, emphasis: 'strong'),
  FiScoreBand(id: 'drift', min: 2, max: 4, label: 'Desvio', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'on-target', min: 0, max: 1, label: 'Na meta', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem meta definida', state: FiState.indeterminate, emphasis: 'muted'),
];

const ({double min, double max}) fiAllocationGapDomain = (min: 0, max: 20);

const List<FiScoreBand> fiGoalProgressBands = [
  FiScoreBand(id: 'reached', min: 100, max: 100, label: 'Meta atingida', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'advancing', min: 50, max: 99, label: 'Mais da metade', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'starting', min: 0, max: 49, label: 'No começo', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem meta definida', state: FiState.indeterminate, emphasis: 'muted'),
];

const ({double min, double max}) fiGoalProgressDomain = (min: 0, max: 100);

const List<FiScoreBand> fiDipScoreBands = [
  FiScoreBand(id: 'opportunity', min: 68, max: 100, label: 'Oportunidade na baixa', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'wait', min: 42, max: 67, label: 'Aguardar', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'trap', min: 0, max: 41, label: 'Armadilha', state: FiState.adverse, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem leitura', state: FiState.indeterminate, emphasis: 'muted'),
];

FiScoreBand fiBandFor(
  double value,
  List<FiScoreBand> bands, [
  double? dataCompleteness,
]) {
  if (!fiScoreIsReliable(dataCompleteness)) {
    return bands.firstWhere((b) => b.min == null, orElse: () => bands.last);
  }
  return bands.firstWhere(
    (b) => b.min != null && value >= b.min!,
    orElse: () => bands.lastWhere((b) => b.min != null, orElse: () => bands.last),
  );
}

abstract final class FiDecision {
  static const interesting = (label: 'Interessante', state: FiState.favorable);
  static const neutral = (label: 'Neutro', state: FiState.neutral);
  static const attention = (label: 'Atenção', state: FiState.attention);
  static const avoid = (label: 'Evitar', state: FiState.adverse);
  static const unknown = (label: 'Sem leitura', state: FiState.indeterminate);
}

abstract final class FiDipDiagnosis {
  static const healthy = (label: 'Queda saudável', criterion: 'preço caiu, fundamentos preservados', state: FiState.favorable);
  static const investigate = (label: 'Queda para investigar', criterion: 'preço caiu e alguma métrica piorou', state: FiState.attention);
  static const structural = (label: 'Queda estrutural', criterion: 'preço caiu junto de deterioração relevante', state: FiState.adverse);
}
