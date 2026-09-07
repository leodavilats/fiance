#!/usr/bin/env node
/**
 * Contraste dos papéis de cor, nos dois temas.
 *
 * A paleta é escrita à mão em `web/src/foundation.css`, e é de lá que este
 * verificador lê — verificado é diferente de recomendado. Um ajuste de paleta que
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
 * **Superfície de estado** (`state-*-surface`) não é medida contra o chão: ela
 * É o chão de um aviso. O que se verifica é o que fica em cima dela — a cor do
 * estado, que escreve o rótulo, e a tinta primária, que escreve o corpo. É a
 * checagem que decide quanta tinta o fundo aguenta antes de comer o texto.
 *
 * **Contorno de controle** (`control-border`) precisa de 3:1 contra o chão e
 * contra a superfície: é o que faz um botão ser um botão, e a WCAG 1.4.11 se
 * aplica a ele. Esta regra não existia, e a consequência era mensurável — o
 * contorno de `.btn-secondary` e `.btn-icon` desenhava a 1,24:1, um quarto do
 * mínimo, porque era `hairline`.
 *
 * **Preenchimento contra poço** (`brand` sobre `track`) também precisa de 3:1:
 * é o par que faz uma barra de progresso mostrar progresso. Sem ele o produto
 * teve uma barra em que preenchido e vazio ficavam a 2,3:1.
 *
 * `hairline` continua de fora de propósito: é separador decorativo, e exigir
 * 3:1 dele produziria uma borda que grita numa interface que depende de
 * silêncio. O que mudou é que separador e contorno de controle deixaram de ser
 * o mesmo token.
 *
 * Uso: `node design-tokens/check-contrast.mjs`
 */

import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const FOUNDATION = resolve(import.meta.dirname, '..', 'web', 'src', 'foundation.css');

/**
 * Lê um bloco de custom properties do CSS escrito à mão.
 *
 * O seletor de tema é a chave: o bloco escuro responde por `:root` e por
 * `[data-theme='dark']` juntos, e o claro aparece duas vezes — uma na consulta
 * de mídia e uma no atributo. Ler o do atributo basta, e é o que o toggle usa.
 */
function lerTema(css, seletor) {
  const inicio = css.indexOf(seletor);
  if (inicio < 0) throw new Error(`seletor ausente em foundation.css: ${seletor}`);
  const abre = css.indexOf('{', inicio);
  const fecha = css.indexOf('\n}', abre);
  const corpo = css.slice(abre + 1, fecha);

  const cores = {};
  for (const [, nome, valor] of corpo.matchAll(/--fi-([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)) {
    cores[nome] = valor;
  }
  return cores;
}

const AA_TEXT = 4.5;
const AA_NON_TEXT = 3.0;

/**
 * O piso do sistema, acima do minimo da norma.
 *
 * A AA e o chao legal, nao o alvo. A paleta chegou a raspar 4,5 em quase todo
 * papel porque a escolha anterior otimizou o lado errado — pegou a maior
 * quantidade de tinta que ainda passava. Aqui cada papel declara a folga que
 * quer, e a escada de tinta e explicita: corpo, secundaria e legenda precisam
 * continuar distinguiveis entre si, senao hierarquia vira uniformidade.
 */
const PISO = {
  'ink-2': 8.0,
  'ink-3': 6.0,
  brand: 6.0,
  'state-': 6.0,
  'direction-': 6.0,
  'series-': 4.5,
};

/** A serie escreve o rotulo do chip de categoria sobre a propria tinta a 15%. */
const CHIP_ALPHA = 0.15;
const CHIP_MIN = 4.5;

function mix(a, b, t) {
  const [ra, ga, ba] = channels(a);
  const [rb, gb, bb] = channels(b);
  const at = v => Math.round(v).toString(16).padStart(2, '0');
  return `#${at(ra + (rb - ra) * t)}${at(ga + (gb - ga) * t)}${at(ba + (bb - ba) * t)}`;
}

function channels(hex) {
  const clean = hex.replace('#', '');
  return [0, 2, 4].map(i => parseInt(clean.slice(i, i + 2), 16));
}

function pisoDe(role) {
  if (PISO[role] !== undefined) return PISO[role];
  const prefixo = Object.keys(PISO).find(k => k.endsWith('-') && role.startsWith(k));
  return prefixo ? PISO[prefixo] : null;
}

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
    if (role.endsWith('-quiet') || role === 'ink-on-brand') continue;
    if (role.startsWith('hairline') || role.startsWith('control-')) continue;
    if (role === 'track' || role === 'ink-disabled') continue;
    if (role.endsWith('-surface')) continue;

    const rule = requirementFor(role);
    if (!rule) continue;

    const piso = pisoDe(role);
    const min = piso ?? rule.min;
    const why = piso ? `${rule.why}; o piso do sistema e ${piso}:1` : rule.why;

    for (const ground of GROUNDS) {
      const ratio = contrast(value, colors[ground]);
      if (ratio + 1e-9 < min) {
        failures.push({ theme, pair: `${role} sobre ${ground}`, ratio, min, why });
      }
    }

    if (role.startsWith('series-')) {
      for (const ground of GROUNDS) {
        const chip = mix(colors[ground], value, CHIP_ALPHA);
        const ratio = contrast(value, chip);
        if (ratio + 1e-9 < CHIP_MIN) {
          failures.push({
            theme,
            pair: `${role} sobre o proprio chip`,
            ratio,
            min: CHIP_MIN,
            why: 'a serie escreve o rotulo do chip de categoria, e ali ela e texto',
          });
        }
      }
    }
  }

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

  for (const [role, value] of Object.entries(colors)) {
    if (!role.endsWith('-surface')) continue;

    const tinta = role.slice(0, -'-surface'.length);
    const pares = [
      [tinta, 'o rótulo do selo é a própria cor do estado'],
      ['ink-1', 'o corpo do aviso é escrito em tinta primária'],
    ];

    for (const [sobre, why] of pares) {
      const min = sobre === 'ink-1' ? 6.0 : 5.5;
      const ratio = contrast(colors[sobre], value);
      if (ratio + 1e-9 < min) {
        failures.push({ theme, pair: `${sobre} sobre ${role}`, ratio, min, why });
      }
    }
  }

  /*
   * Contorno, poco e preenchimento — o que a regua antiga nao cobria.
   *
   * As tres primeiras linhas existem porque a paleta reprovava nelas: o
   * contorno de controle desenhava a 1,24:1 herdando `hairline`, e o
   * preenchimento de uma barra ficava a 2,28:1 do proprio poco. Nenhuma
   * revisao visual pega isso; a conta pega.
   */
  const naoTexto = [
    ['control-border', 'ground-0', 'e o contorno que faz um controle ser um controle (WCAG 1.4.11)'],
    ['control-border', 'ground-1', 'o mesmo contorno, sobre superficie'],
    ['control-border-hover', 'ground-1', 'o contorno sob o ponteiro nao pode piorar'],
    ['brand', 'track', 'preenchido contra vazio: e o par que faz progresso ser legivel'],
  ];

  /*
   * O poco NAO e medido contra o chao de proposito.
   *
   * A extensao de uma regua ou de uma barra vem do contorno, que ja e cobrado
   * acima; o poco e o vazio dentro dele. Exigir 3:1 do poco tambem obrigaria a
   * escurecer o vazio ate ele competir com o preenchido, que e o oposto do que
   * se quer ler.
   */
  for (const [papel, contra, why] of naoTexto) {
    const ratio = contrast(colors[papel], colors[contra]);
    if (ratio + 1e-9 < AA_NON_TEXT) {
      failures.push({ theme, pair: `${papel} sobre ${contra}`, ratio, min: AA_NON_TEXT, why });
    }
  }

  /* Rotulo sobre os preenchimentos de controle, nos tres estados. */
  for (const fundo of ['control-fill', 'control-fill-hover', 'control-fill-active']) {
    const ratio = contrast(colors['ink-1'], colors[fundo]);
    if (ratio + 1e-9 < AA_TEXT) {
      failures.push({
        theme,
        pair: `ink-1 sobre ${fundo}`,
        ratio,
        min: AA_TEXT,
        why: 'e o rotulo do botao secundario, e ele nao muda de cor ao ser pressionado',
      });
    }
  }

  /* O texto do botao primario nos tres estados, nao so no de repouso. */
  for (const fundo of ['brand', 'brand-hover', 'brand-active']) {
    const ratio = contrast(colors['ink-on-brand'], colors[fundo]);
    if (ratio + 1e-9 < AA_TEXT) {
      failures.push({
        theme,
        pair: `ink-on-brand sobre ${fundo}`,
        ratio,
        min: AA_TEXT,
        why: 'o rotulo do botao primario tem de continuar legivel sob ponteiro e ao ser pressionado',
      });
    }
  }

  /*
   * Tinta desabilitada.
   *
   * `opacity: 0.5` era o truque anterior, e ele derruba o contraste do texto
   * junto com o do fundo. A norma isenta controle desabilitado, e o produto
   * nao: inerte tem de continuar legivel, senao a pessoa nao sabe o que o
   * botao faria.
   */
  const inerte = contrast(colors['ink-disabled'], colors['control-fill']);
  if (inerte + 1e-9 < AA_NON_TEXT) {
    failures.push({
      theme,
      pair: 'ink-disabled sobre control-fill',
      ratio: inerte,
      min: AA_NON_TEXT,
      why: 'controle inerte continua tendo de ser lido',
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
  const css = readFileSync(FOUNDATION, 'utf8');
  const paleta = {
    dark: lerTema(css, ":root[data-theme='dark']"),
    light: lerTema(css, ":root[data-theme='light']"),
  };

  const failures = [];

  /*
   * Papel definido num tema e não no outro.
   *
   * Com a paleta gerada de um JSON com duas chaves irmãs isso era difícil de
   * fazer; escrita à mão em três blocos, é a divergência mais provável — e o
   * sintoma é uma cor que simplesmente não existe num dos temas.
   */
  const soNoEscuro = Object.keys(paleta.dark).filter(k => !(k in paleta.light));
  const soNoClaro = Object.keys(paleta.light).filter(k => !(k in paleta.dark));
  for (const [papeis, onde] of [
    [soNoEscuro, 'escuro'],
    [soNoClaro, 'claro'],
  ]) {
    for (const papel of papeis) {
      failures.push({
        theme: onde,
        pair: papel,
        ratio: 0,
        min: 0,
        why: `declarado só no tema ${onde}; papel de cor existe nos dois ou em nenhum`,
      });
    }
  }

  for (const theme of ['dark', 'light']) {
    failures.push(...check(theme, paleta[theme]));
  }

  if (failures.length > 0) {
    console.error('\n✗ Contraste abaixo do mínimo WCAG AA\n');
    for (const f of failures) {
      console.error(
        `  [${f.theme}] ${f.pair}: ${f.ratio.toFixed(2)}:1, mínimo ${f.min}:1 — ${f.why}`
      );
    }
    console.error(
      '\n  Ajuste a cor em web/src/foundation.css — e no espelho em' +
        '\n  mobile/lib/core/design_tokens.dart, que nenhuma maquina confere.' +
        '\n  Afrouxar o limiar não é opção: a diferença entre 4,4 e 4,6 não se enxerga' +
        '\n  em revisão, mas separa quem lê a tela de quem não lê.\n'
    );
    process.exit(1);
  }

  console.log('✓ Contraste em AA nos dois temas.');
}

main();
