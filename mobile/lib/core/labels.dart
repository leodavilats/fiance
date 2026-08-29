import 'package:flutter/material.dart';

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

IconData categoryIcon(String? category) {
  final chave = fiCategoriaApelidos[category] ?? category;
  return fiCategorias[chave]?.icon ?? Icons.category_outlined;
}

Color sectorColor(String sector, Brightness brightness) =>
    fiSeriesColor(fiSetorSeriePorRotulo[sector] ?? 0, brightness);
