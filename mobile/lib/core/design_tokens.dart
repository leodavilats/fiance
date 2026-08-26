// GERADO AUTOMATICAMENTE — NÃO EDITE ESTE ARQUIVO.
// Fonte: design-tokens/tokens.json · Gerador: design-tokens/build.mjs
// Regenerar: node design-tokens/build.mjs

import 'package:flutter/material.dart';

/// Espelha `web/src/tokens.css` e `web/src/app/core/design-tokens.ts` — os três
/// saem de `design-tokens/tokens.json`, então não podem divergir.
abstract final class FiColors {
  static const darkGround0 = Color(0xFF0E1211);
  static const darkGround1 = Color(0xFF141917);
  static const darkGround2 = Color(0xFF1A201E);
  static const darkHairline = Color(0xFF262D2A);
  static const darkHairlineStrong = Color(0xFF333B38);
  static const darkInk1 = Color(0xFFE9EAE9);
  static const darkInk2 = Color(0xFFA5ACA9);
  static const darkInk3 = Color(0xFF7B8380);
  static const darkInkOnBrand = Color(0xFF08131A);
  static const darkBrand = Color(0xFF5B9DC0);
  static const darkBrandQuiet = Color(0xFF1D3140);
  static const darkStateFavorable = Color(0xFF4FB286);
  static const darkStateAttention = Color(0xFFD9A23B);
  static const darkStateAdverse = Color(0xFFD9705F);
  static const darkStateIndeterminate = Color(0xFF7B8380);
  static const darkDirectionUp = Color(0xFF5E8F79);
  static const darkDirectionDown = Color(0xFFA8756B);
  static const darkSeries1 = Color(0xFF5B9DC0);
  static const darkSeries2 = Color(0xFF4FB286);
  static const darkSeries3 = Color(0xFFD9A23B);
  static const darkSeries4 = Color(0xFFD9705F);
  static const darkSeries5 = Color(0xFF9084C4);
  static const darkSeries6 = Color(0xFF3FA3A3);
  static const darkSeries7 = Color(0xFFD07FA8);
  static const darkSeries8 = Color(0xFFD2874F);
  static const darkSeries9 = Color(0xFF96A94F);
  static const darkSeries10 = Color(0xFF6E8FD6);
  static const darkSeries11 = Color(0xFFB5849B);
  static const darkSeriesOther = Color(0xFF5A6360);

  static const lightGround0 = Color(0xFFFAF8F5);
  static const lightGround1 = Color(0xFFFFFFFF);
  static const lightGround2 = Color(0xFFF3F0EB);
  static const lightHairline = Color(0xFFE2DDD5);
  static const lightHairlineStrong = Color(0xFFCFC8BD);
  static const lightInk1 = Color(0xFF1C1F1E);
  static const lightInk2 = Color(0xFF55605C);
  static const lightInk3 = Color(0xFF656F6A);
  static const lightInkOnBrand = Color(0xFFFFFFFF);
  static const lightBrand = Color(0xFF2C6485);
  static const lightBrandQuiet = Color(0xFFE4EDF2);
  static const lightStateFavorable = Color(0xFF157F58);
  static const lightStateAttention = Color(0xFF8C5C10);
  static const lightStateAdverse = Color(0xFFB04434);
  static const lightStateIndeterminate = Color(0xFF656F6A);
  static const lightDirectionUp = Color(0xFF3F7A61);
  static const lightDirectionDown = Color(0xFF8E5A4C);
  static const lightSeries1 = Color(0xFF2C6485);
  static const lightSeries2 = Color(0xFF157F58);
  static const lightSeries3 = Color(0xFF8C5C10);
  static const lightSeries4 = Color(0xFFB04434);
  static const lightSeries5 = Color(0xFF5C51A0);
  static const lightSeries6 = Color(0xFF17706F);
  static const lightSeries7 = Color(0xFF96436B);
  static const lightSeries8 = Color(0xFFA05A1F);
  static const lightSeries9 = Color(0xFF5C6B1E);
  static const lightSeries10 = Color(0xFF3B5AA8);
  static const lightSeries11 = Color(0xFF7A4E62);
  static const lightSeriesOther = Color(0xFF8A938E);

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

Color fiDirectionColor(double delta, Brightness brightness) {
  final dark = brightness == Brightness.dark;
  if (delta > 0) return dark ? FiColors.darkDirectionUp : FiColors.lightDirectionUp;
  if (delta < 0) return dark ? FiColors.darkDirectionDown : FiColors.lightDirectionDown;
  return dark ? FiColors.darkInk2 : FiColors.lightInk2;
}

/// Identidade de série (1..N). Mesmo setor/classe = mesma cor sempre.
///
/// Fora da faixa cai em `series-other`, que é o balde de "Outros" — não
/// uma cor de erro.
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

/// Régua do score — espelha `backend/app/analysis/score_ruler.py`.
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
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Dado insuficiente', state: FiState.indeterminate, emphasis: 'muted'),
];

abstract final class FiScoreRulerSize {
  static const inline = 16.0;
  static const list = 24.0;
  static const card = 40.0;
  static const page = 64.0;
}

/// Dado incompleto não pode parecer nota baixa — sai cinza e rotulado.
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
