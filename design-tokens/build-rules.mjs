#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..');
const tokens = JSON.parse(readFileSync(join(here, 'product-rules.json'), 'utf8'));

const CHECK = process.argv.includes('--check');
const BANNER_LINES = [
  'GERADO AUTOMATICAMENTE — NÃO EDITE ESTE ARQUIVO.',
  'Fonte: design-tokens/product-rules.json · Gerador: design-tokens/build-rules.mjs',
  'Regenerar: node design-tokens/build-rules.mjs',
];

const isMeta = k => k.startsWith('$') || k === 'meta';
const entries = obj => Object.entries(obj).filter(([k]) => !isMeta(k));
const kebabToCamel = s => s.replace(/-([a-z0-9])/g, (_, c) => c.toUpperCase());
const kebabToPascal = s => {
  const c = kebabToCamel(s);
  return c.charAt(0).toUpperCase() + c.slice(1);
};
const camelToKebab = s => s.replace(/[A-Z]/g, c => `-${c.toLowerCase()}`);

/**
 * As réguas derivadas do `scoreRuler`: mesma mecânica (valor numa escala com
 * zonas nomeadas), leituras diferentes. `scoreRuler` fica de fora porque é o
 * único cujos limiares espelham o backend — os demais são apresentação.
 */
const derivedRulers = () =>
  Object.keys(tokens)
    .filter(k => k.endsWith('Ruler') && k !== 'scoreRuler' && !isMeta(k))
    .map(key => ({
      key,
      /** `healthRuler` → `Health`, `marginOfSafetyRuler` → `MarginOfSafety`. */
      name: key.slice(0, -'Ruler'.length).replace(/^./, c => c.toUpperCase()),
      spec: tokens[key],
    }));

function buildTs() {
  const out = [];

  out.push(
    "export type FiState = 'favorable' | 'attention' | 'adverse' | 'neutral' | 'indeterminate';",
    ''
  );

  const r = tokens.scoreRuler;
  out.push(`export const SCORE_STRONG = ${r.thresholds.strong};`);
  out.push(`export const SCORE_GOOD = ${r.thresholds.good};`);
  out.push(`export const SCORE_NEUTRAL = ${r.thresholds.neutral};`);
  out.push(`export const MIN_DATA_COMPLETENESS = ${r.minDataCompleteness};`);
  out.push(`export const HIGHLIGHT_MIN_DY = ${r.highlightMinDy};`, '');

  out.push('export interface FiScoreBand {');
  out.push("  readonly id: string;");
  out.push('  readonly min: number | null;');
  out.push('  readonly max: number | null;');
  out.push('  readonly label: string;');
  out.push('  readonly state: FiState;');
  out.push("  readonly emphasis: 'strong' | 'muted';");
  out.push('}', '');

  out.push('export const fiScoreBands: readonly FiScoreBand[] = [');
  for (const b of r.bands) {
    out.push(
      `  { id: '${b.id}', min: ${b.min}, max: ${b.max}, label: '${b.label}', state: '${b.state}', emphasis: '${b.emphasis}' },`
    );
  }
  out.push('] as const;', '');

  out.push('export const fiScoreRulerSizes = {');
  for (const [k, v] of entries(r.sizes)) out.push(`  ${k}: ${v},`);
  out.push('} as const;', '');

  out.push('export function fiScoreIsReliable(dataCompleteness?: number | null): boolean {');
  out.push('  return (dataCompleteness ?? 1) >= MIN_DATA_COMPLETENESS;');
  out.push('}', '');

  out.push('export function fiScoreBandFor(');
  out.push('  score: number,');
  out.push('  dataCompleteness?: number | null');
  out.push('): FiScoreBand {');
  out.push('  if (!fiScoreIsReliable(dataCompleteness)) {');
  out.push("    return fiScoreBands.find(b => b.id === 'insufficient')!;");
  out.push('  }');
  out.push('  return (');
  out.push('    fiScoreBands.find(b => b.min !== null && score >= b.min) ??');
  out.push("    fiScoreBands.find(b => b.id === 'weak')!");
  out.push('  );');
  out.push('}', '');
  for (const { name, spec } of derivedRulers()) {
    out.push(`export const fi${name}Bands: readonly FiScoreBand[] = [`);
    for (const b of spec.bands) {
      out.push(
        `  { id: '${b.id}', min: ${b.min}, max: ${b.max}, label: '${b.label}', state: '${b.state}', emphasis: '${b.emphasis}' },`
      );
    }
    out.push('] as const;', '');
    if (spec.domain) {
      out.push(
        `export const fi${name}Domain = { min: ${spec.domain.min}, max: ${spec.domain.max} } as const;`,
        ''
      );
    }
  }
  out.push('export function fiBandFor(');
  out.push('  value: number,');
  out.push('  bands: readonly FiScoreBand[],');
  out.push('  dataCompleteness?: number | null');
  out.push('): FiScoreBand {');
  out.push('  if (!fiScoreIsReliable(dataCompleteness)) {');
  out.push("    return bands.find(b => b.min === null) ?? bands[bands.length - 1];");
  out.push('  }');
  out.push('  return (');
  out.push('    bands.find(b => b.min !== null && value >= b.min) ??');
  out.push('    bands.filter(b => b.min !== null).slice(-1)[0] ??');
  out.push('    bands[bands.length - 1]');
  out.push('  );');
  out.push('}', '');
  out.push('export const fiDecision = {');
  for (const [k, v] of entries(tokens.decision)) {
    out.push(`  ${k}: { label: '${v.label}', state: '${v.state}' as FiState },`);
  }
  out.push('} as const;', '');

  out.push('export const fiDipDiagnosis = {');
  for (const [k, v] of entries(tokens.dipDiagnosis)) {
    out.push(
      `  ${k}: { label: '${v.label}', criterion: '${v.criterion}', state: '${v.state}' as FiState },`
    );
  }
  out.push('} as const;', '');

  return out.join('\n');
}

const dartColor = hex => `Color(0xFF${hex.replace('#', '').toUpperCase()})`;

function buildDart() {
  const out = [];
  out.push('enum FiState { favorable, attention, adverse, neutral, indeterminate }', '');
  const r = tokens.scoreRuler;
  out.push(`const double kScoreStrong = ${r.thresholds.strong};`);
  out.push(`const double kScoreGood = ${r.thresholds.good};`);
  out.push(`const double kScoreNeutral = ${r.thresholds.neutral};`);
  out.push(`const double kMinDataCompleteness = ${r.minDataCompleteness};`);
  out.push(`const double kHighlightMinDy = ${r.highlightMinDy};`, '');

  out.push('class FiScoreBand {');
  out.push('  const FiScoreBand({');
  out.push('    required this.id,');
  out.push('    required this.min,');
  out.push('    required this.max,');
  out.push('    required this.label,');
  out.push('    required this.state,');
  out.push('    required this.emphasis,');
  out.push('  });', '');
  out.push('  final String id;');
  out.push('  final double? min;');
  out.push('  final double? max;');
  out.push('  final String label;');
  out.push('  final FiState state;');
  out.push('  final String emphasis;');
  out.push('}', '');

  out.push('const List<FiScoreBand> fiScoreBands = [');
  for (const b of r.bands) {
    const state = b.state === 'neutral' ? 'neutral' : b.state;
    out.push(
      `  FiScoreBand(id: '${b.id}', min: ${b.min === null ? 'null' : `${b.min}`}, max: ${b.max === null ? 'null' : `${b.max}`}, label: '${b.label}', state: FiState.${state}, emphasis: '${b.emphasis}'),`
    );
  }
  out.push('];', '');

  out.push('abstract final class FiScoreRulerSize {');
  for (const [k, v] of entries(r.sizes)) out.push(`  static const ${k} = ${v}.0;`);
  out.push('}', '');

  out.push('bool fiScoreIsReliable(double? dataCompleteness) =>');
  out.push('    (dataCompleteness ?? 1) >= kMinDataCompleteness;', '');

  out.push('FiScoreBand fiScoreBandFor(double score, double? dataCompleteness) {');
  out.push('  if (!fiScoreIsReliable(dataCompleteness)) {');
  out.push("    return fiScoreBands.firstWhere((b) => b.id == 'insufficient');");
  out.push('  }');
  out.push('  return fiScoreBands.firstWhere(');
  out.push('    (b) => b.min != null && score >= b.min!,');
  out.push("    orElse: () => fiScoreBands.firstWhere((b) => b.id == 'weak'),");
  out.push('  );');
  out.push('}', '');
  for (const { name, spec } of derivedRulers()) {
    const lower = name.charAt(0).toLowerCase() + name.slice(1);
    out.push(`const List<FiScoreBand> fi${name}Bands = [`);
    for (const b of spec.bands) {
      out.push(
        `  FiScoreBand(id: '${b.id}', min: ${b.min === null ? 'null' : `${b.min}`}, max: ${b.max === null ? 'null' : `${b.max}`}, label: '${b.label}', state: FiState.${b.state}, emphasis: '${b.emphasis}'),`
      );
    }
    out.push('];', '');
    if (spec.domain) {
      out.push(
        `const ({double min, double max}) fi${name}Domain = (min: ${spec.domain.min}, max: ${spec.domain.max});`,
        ''
      );
    }
  }
  out.push('FiScoreBand fiBandFor(');
  out.push('  double value,');
  out.push('  List<FiScoreBand> bands, [');
  out.push('  double? dataCompleteness,');
  out.push(']) {');
  out.push('  if (!fiScoreIsReliable(dataCompleteness)) {');
  out.push('    return bands.firstWhere((b) => b.min == null, orElse: () => bands.last);');
  out.push('  }');
  out.push('  return bands.firstWhere(');
  out.push('    (b) => b.min != null && value >= b.min!,');
  out.push('    orElse: () => bands.lastWhere((b) => b.min != null, orElse: () => bands.last),');
  out.push('  );');
  out.push('}', '');
  out.push('abstract final class FiDecision {');
  for (const [k, v] of entries(tokens.decision)) {
    out.push(
      `  static const ${kebabToCamel(k)} = (label: '${v.label}', state: FiState.${v.state});`
    );
  }
  out.push('}', '');

  out.push('abstract final class FiDipDiagnosis {');
  for (const [k, v] of entries(tokens.dipDiagnosis)) {
    out.push(
      `  static const ${kebabToCamel(k)} = (label: '${v.label}', criterion: '${v.criterion}', state: FiState.${v.state});`
    );
  }
  out.push('}', '');

  return out.join('\n');
}

const aspas = v => `'${String(v).replace(/'/g, "\'")}'`;

const chave = k => (/^[\p{L}_$][\p{L}\p{N}_$]*$/u.test(k) ? k : aspas(k));

function buildVocabTs() {
  const v = tokens.vocabulary;
  const linhas = [];


  linhas.push('export interface FiCategoria {');
  linhas.push('  readonly label: string;');
  linhas.push('  readonly series: number;');
  linhas.push('  readonly icon: string;');
  linhas.push('}');
  linhas.push('');

  linhas.push('export const fiCategorias: Readonly<Record<string, FiCategoria>> = {');
  for (const [id, c] of entries(v.categories)) {
    linhas.push(`  ${id}: { label: ${aspas(c.label)}, series: ${c.series}, icon: ${aspas(c.web)} },`);
  }
  linhas.push('};');
  linhas.push('');

  linhas.push('export const fiCategoriaApelidos: Readonly<Record<string, string>> = {');
  for (const [de, para] of entries(v.categoryAliases)) linhas.push(`  ${de}: ${aspas(para)},`);
  linhas.push('};');
  linhas.push('');

  linhas.push('export const fiTiposDeAtivo: Readonly<Record<string, { label: string; category: string }>> = {');
  for (const [id, t] of entries(v.assetTypes)) {
    linhas.push(`  ${id}: { label: ${aspas(t.label)}, category: ${aspas(t.category)} },`);
  }
  linhas.push('};');
  linhas.push('');

  linhas.push('export const fiSetores: Readonly<Record<string, { label: string; series: number }>> = {');
  for (const [id, sec] of entries(v.sectors)) {
    linhas.push(`  ${chave(id)}: { label: ${aspas(sec.label)}, series: ${sec.series} },`);
  }
  linhas.push('};');
  linhas.push('');

  linhas.push('export const fiSetorApelidos: Readonly<Record<string, string>> = {');
  for (const [de, para] of entries(v.sectorAliases)) {
    linhas.push(`  ${chave(de)}: ${aspas(para)},`);
  }
  linhas.push('};');
  linhas.push('');

  linhas.push('export const fiSetorSeriePorRotulo: Readonly<Record<string, number>> = {');
  for (const [, sec] of entries(v.sectors)) {
    linhas.push(`  ${chave(sec.label)}: ${sec.series},`);
  }
  linhas.push('};');
  linhas.push('');

  linhas.push('export const fiTiposDeRendaFixa: Readonly<Record<string, string>> = {');
  for (const [id, label] of entries(v.fixedIncomeTypes)) linhas.push(`  ${id}: ${aspas(label)},`);
  linhas.push('};');
  linhas.push('');

  linhas.push('export const fiLiquidez: Readonly<Record<string, string>> = {');
  for (const [id, label] of entries(v.liquidity)) linhas.push(`  ${id}: ${aspas(label)},`);
  linhas.push('};');
  linhas.push('');

  const seriesUsadas = [...new Set(entries(v.categories).map(([, c]) => c.series))].sort((a, b) => a - b);
  const mapasDeClasse = [
    ['fiClasseTextoDaSerie', 'text-series-', ''],
    ['fiClasseFundoDaSerie', 'bg-series-', ''],
    ['fiClasseBarraDaSerie', 'bg-series-', ''],
    ['fiClasseChipDaSerie', 'bg-series-', '/15'],
    ['fiClasseBordaDaSerie', 'border-series-', '/30'],
  ];

  for (const [nome, prefixo, sufixo] of mapasDeClasse) {
    linhas.push(`export const ${nome}: Readonly<Record<number, string>> = {`);
    for (const n of seriesUsadas) {
      linhas.push(`  ${n}: '${prefixo}${n === 0 ? 'other' : n}${sufixo}',`);
    }
    linhas.push('};');
    linhas.push('');
  }

  return linhas.join('\n');
}

const dartIcone = nome => `Icons.${nome}`;

function buildVocabDart() {
  const v = tokens.vocabulary;
  const linhas = [];

  linhas.push("import 'package:flutter/material.dart';", '');

  linhas.push('class FiCategoria {');
  linhas.push('  const FiCategoria(this.label, this.series, this.icon);');
  linhas.push('');
  linhas.push('  final String label;');
  linhas.push('  final int series;');
  linhas.push('  final IconData icon;');
  linhas.push('}');
  linhas.push('');

  linhas.push('const Map<String, FiCategoria> fiCategorias = {');
  for (const [id, c] of entries(v.categories)) {
    linhas.push(`  '${id}': FiCategoria('${c.label}', ${c.series}, ${dartIcone(c.mobile)}),`);
  }
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, String> fiCategoriaApelidos = {');
  for (const [de, para] of entries(v.categoryAliases)) linhas.push(`  '${de}': '${para}',`);
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, String> fiTiposDeAtivo = {');
  for (const [id, t] of entries(v.assetTypes)) linhas.push(`  '${id}': '${t.label}',`);
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, String> fiTipoDeAtivoParaCategoria = {');
  for (const [id, t] of entries(v.assetTypes)) linhas.push(`  '${id}': '${t.category}',`);
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, String> fiSetores = {');
  for (const [id, sec] of entries(v.sectors)) linhas.push(`  '${id}': '${sec.label}',`);
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, String> fiSetorApelidos = {');
  for (const [de, para] of entries(v.sectorAliases)) linhas.push(`  '${de}': '${para}',`);
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, int> fiSetorSeriePorRotulo = {');
  for (const [, sec] of entries(v.sectors)) linhas.push(`  '${sec.label}': ${sec.series},`);
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, String> fiTiposDeRendaFixa = {');
  for (const [id, label] of entries(v.fixedIncomeTypes)) linhas.push(`  '${id}': '${label}',`);
  linhas.push('};');
  linhas.push('');

  linhas.push('const Map<String, String> fiLiquidez = {');
  for (const [id, label] of entries(v.liquidity)) linhas.push(`  '${id}': '${label}',`);
  linhas.push('};');

  return linhas.join('\n');
}

const artifacts = [
  { path: join(repo, 'web', 'src', 'app', 'core', 'product-rules.ts'), content: buildTs() },
  { path: join(repo, 'mobile', 'lib', 'core', 'product_rules.dart'), content: buildDart() },
  { path: join(repo, 'web', 'src', 'app', 'core', 'vocabulary.ts'), content: buildVocabTs() },
  { path: join(repo, 'mobile', 'lib', 'core', 'vocabulary.dart'), content: buildVocabDart() },
];

/**
 * O aviso de arquivo gerado.
 *
 * As quatro saidas nasceram sem marca nenhuma, e `BANNER_LINES` existia declarado e nao
 * usado desde o primeiro commit do gerador. Arquivo gerado sem aviso e arquivo que alguem
 * edita a mao, e a edicao volta no proximo `--check` como divergencia sem causa aparente.
 */
const banner = `${BANNER_LINES.map(l => `// ${l}`).join('\n')}\n\n`;

let drift = 0;
for (const { path, content } of artifacts) {
  const body = `${banner}${content.endsWith('\n') ? content : `${content}\n`}`;
  const rel = path.slice(repo.length + 1).replace(/\\/g, '/');
  if (CHECK) {
    const current = existsSync(path) ? readFileSync(path, 'utf8') : null;
    if (current !== body) {
      console.error(`✗ fora de sincronia: ${rel}`);
      drift += 1;
    } else {
      console.log(`✓ ${rel}`);
    }
    continue;
  }
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, body, 'utf8');
  console.log(`escrito ${rel} (${body.split('\n').length} linhas)`);
}

if (CHECK && drift > 0) {
  console.error(
    `\n${drift} arquivo(s) divergem de design-tokens/product-rules.json.\n` +
      'Rode `node design-tokens/build-rules.mjs` e faça commit do resultado.'
  );
  process.exit(1);
}
