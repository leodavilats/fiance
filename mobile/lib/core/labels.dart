import 'package:flutter/material.dart';

import 'cash_models.dart';
import 'design_tokens.dart';
import 'vocabulary.dart';

String rendaFixaTipoLabel(String? tipo) {
  if (tipo == null) return '—';
  return fiTiposDeRendaFixa[tipo] ?? tipo;
}

String liquidezLabel(String? liquidez) =>
    fiLiquidez[liquidez] ?? fiLiquidez['no_vencimento']!;

String categoryLabel(String? category) {
  if (category == null) return '—';
  final chave = fiCategoriaApelidos[category] ?? category;
  return fiCategorias[chave]?.label ?? category;
}

String assetTypeLabel(String? assetType) {
  if (assetType == null) return '—';
  return fiTiposDeAtivo[assetType] ?? assetType;
}

Color categoryColor(String? category, Brightness brightness) {
  final chave = fiCategoriaApelidos[category] ?? category;
  return fiSeriesColor(fiCategorias[chave]?.series ?? 0, brightness);
}

Color sectorColor(String sector, Brightness brightness) =>
    fiSeriesColor(fiSetorSeriePorRotulo[sector] ?? 0, brightness);

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



Map<String, FiCategoria> _mapaDe(CashKind kind) =>
    kind == CashKind.income ? fiCategoriasDeEntrada : fiCategoriasDeDespesa;

String cashCategoryLabel(CashKind kind, String? category) {
  if (category == null) return '—';
  return _mapaDe(kind)[category]?.label ?? category;
}

List<String> cashCategoryKeys(CashKind kind) {
  final mapa = _mapaDe(kind);
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
  return fiTiposDeDivida[kind] ?? kind;
}
