#!/usr/bin/env node
/**
 * Contraste dos papéis de cor, nos dois temas.
 *
 * Cor é gerada de `tokens.json`, então contraste também pode ser **verificado**
 * de lá — e verificado é diferente de recomendado. Um ajuste de paleta que
 * derruba um par abaixo do mínimo passa despercebido em revisão visual: a
 * diferença entre 4,4 e 4,6 não se enxerga, mas separa quem lê a tela de quem
 * não lê.
 *
 * Os limiares são os da WCAG 2.1 AA, aplicados ao que cada papel de fato é:
 *
 * * **Texto** (`ink-*`, `state-*`, `direction-*`) precisa de 4,5:1. Inclui
 *   `ink-3`, que é legenda: legenda é texto pequeno, e a regra para texto
 *   pequeno é mais rígida, não menos.
 * * **Superfície interativa** (`brand` como fundo, `ink-on-brand` sobre ele)
 *   também precisa de 4,5:1, porque ali há texto.
 * * **Séries de gráfico** precisam de 3:1 contra o fundo — são forma, não
 *   texto, e a WCAG 1.4.11 é a regra que se aplica. Elas **nunca** são a única
 *   informação: o gráfico tem alternativa textual.
 *
 * `hairline` fica de fora de propósito: é separador decorativo, e exigir 3:1
 * dele produziria uma borda que grita numa interface que depende de silêncio.
 *
 * Uso: `node design-tokens/check-contrast.mjs`
 */

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const TOKENS = join(import.meta.dirname, 'tokens.json');

const AA_TEXT = 4.5;
const AA_NON_TEXT = 3.0;

/** Superfícies sobre as quais tudo é desenhado. */
const GROUNDS = ['ground-0', 'ground-1', 'ground-2'];

function channel(value) {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex) {
  const clean = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map(i => channel(parseInt(clean.slice(i, i + 2), 16)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const [x, y] = [luminance(a), luminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

/** O que cada papel exige, e por quê — a razão vai na mensagem de falha. */
function requirementFor(role) {
  if (role.startsWith('series-')) {
    return { min: AA_NON_TEXT, why: 'série de gráfico é forma (WCAG 1.4.11)' };
  }
  if (role.startsWith('ink-') || role.startsWith('state-') || role.startsWith('direction-')) {
    return { min: AA_TEXT, why: 'é usado como texto' };
  }
  if (role === 'brand') {
    return { min: AA_TEXT, why: 'carrega texto e ação' };
  }
  return null;
}

function check(theme, colors) {
  const failures = [];

  for (const [role, value] of Object.entries(colors)) {
    if (role.startsWith('$') || GROUNDS.includes(role)) continue;
    // `*-quiet` é fundo de destaque, não primeiro plano: ele é verificado do
    // outro lado, como superfície de `ink-1`.
    if (role.endsWith('-quiet') || role === 'ink-on-brand') continue;
    if (role.startsWith('hairline')) continue;

    const rule = requirementFor(role);
    if (!rule) continue;

    for (const ground of GROUNDS) {
      const ratio = contrast(value, colors[ground]);
      if (ratio + 1e-9 < rule.min) {
        failures.push({
          theme,
          pair: `${role} sobre ${ground}`,
          ratio,
          min: rule.min,
          why: rule.why,
        });
      }
    }
  }

  // Texto sobre superfície de marca, dos dois lados.
  const sobreMarca = contrast(colors['ink-on-brand'], colors.brand);
  if (sobreMarca + 1e-9 < AA_TEXT) {
    failures.push({
      theme,
      pair: 'ink-on-brand sobre brand',
      ratio: sobreMarca,
      min: AA_TEXT,
      why: 'é o texto do botão primário',
    });
  }

  const emQuiet = contrast(colors['ink-1'], colors['brand-quiet']);
  if (emQuiet + 1e-9 < AA_TEXT) {
    failures.push({
      theme,
      pair: 'ink-1 sobre brand-quiet',
      ratio: emQuiet,
      min: AA_TEXT,
      why: 'brand-quiet é fundo de destaque com texto dentro',
    });
  }

  return failures;
}

function main() {
  const tokens = JSON.parse(readFileSync(TOKENS, 'utf8'));
  const failures = [];

  for (const theme of ['dark', 'light']) {
    failures.push(...check(theme, tokens.color[theme]));
  }

  if (failures.length > 0) {
    console.error('\n✗ Contraste abaixo do mínimo WCAG AA\n');
    for (const f of failures) {
      console.error(
        `  [${f.theme}] ${f.pair}: ${f.ratio.toFixed(2)}:1, mínimo ${f.min}:1 — ${f.why}`
      );
    }
    console.error(
      '\n  Ajuste a cor em design-tokens/tokens.json e rode `node design-tokens/build.mjs`.' +
        '\n  Afrouxar o limiar não é opção: a diferença entre 4,4 e 4,6 não se enxerga' +
        '\n  em revisão, mas separa quem lê a tela de quem não lê.\n'
    );
    process.exit(1);
  }

  console.log('✓ Contraste em AA nos dois temas.');
}

main();
