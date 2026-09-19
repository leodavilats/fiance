import 'package:flutter/material.dart';

import 'cash_models.dart';
import 'design_tokens.dart';
import 'vocabulary.dart';

String fixedIncomeKindLabel(String? kind) {
  if (kind == null) return '—';
  return fiFixedIncomeKinds[kind] ?? kind;
}

String fixedIncomeLiquidityLabel(String? liquidity) =>
    fiLiquidity[liquidity] ?? fiLiquidity['no_vencimento']!;

String categoryLabel(String? category) {
  if (category == null) return '—';
  final chave = fiCategoryAliases[category] ?? category;
  return fiCategories[chave]?.label ?? category;
}

String assetTypeLabel(String? assetType) {
  if (assetType == null) return '—';
  return fiAssetTypes[assetType] ?? assetType;
}

Color categoryColor(String? category, Brightness brightness) {
  final chave = fiCategoryAliases[category] ?? category;
  return fiSeriesColor(fiCategories[chave]?.series ?? 0, brightness);
}

Color sectorColor(String sector, Brightness brightness) =>
    fiSeriesColor(fiSectorSeriesByLabel[sector] ?? 0, brightness);

FiState fiVerdictState(String? verdict) {
  final v = verdict ?? '';
  if (v.contains('BUY')) return FiState.favorable;
  if (v.contains('SELL')) return FiState.adverse;
  return FiState.indeterminate;
}

FiState fiSeverityState(String? severity) {
  switch (severity) {
    case 'critical':
    case 'high':
      return FiState.adverse;
    case 'warning':
    case 'medium':
      return FiState.attention;
    case 'positive':
      return FiState.favorable;
    default:
      return FiState.indeterminate;
  }
}

String trendLabel(String? trend) {
  switch (trend) {
    case 'uptrend':
      return '↗ Alta';
    case 'downtrend':
      return '↘ Baixa';
    case 'sideways':
      return '→ Lateral';
    default:
      return 'sem histórico suficiente';
  }
}



Map<String, FiCategory> _mapOf(CashKind kind) =>
    kind == CashKind.income ? fiIncomeCategories : fiExpenseCategories;

String cashCategoryLabel(CashKind kind, String? category) {
  if (category == null) return '—';
  return _mapOf(kind)[category]?.label ?? category;
}

List<String> cashCategoryKeys(CashKind kind) {
  final mapa = _mapOf(kind);
  return mapa.keys.toList()
    ..sort((a, b) {
      final sa = mapa[a]!.series;
      final sb = mapa[b]!.series;
      if (sa == 0) return 1;
      if (sb == 0) return -1;
      return sa.compareTo(sb);
    });
}

String debtKindLabel(String? kind) {
  if (kind == null) return '—';
  return fiDebtKinds[kind] ?? kind;
}

String ledgerKindLabel(String? kind) {
  if (kind == null) return '—';
  return fiLedgerKinds[kind] ?? kind;
}

String ledgerKindExplanation(String? kind) {
  if (kind == null) return '';
  return fiLedgerKindExplanations[kind] ?? '';
}

String dividendKindLabel(String? kind) {
  if (kind == null) return '—';
  return fiDividendKinds[kind] ?? kind;
}
