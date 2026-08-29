#!/usr/bin/env node

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';

const WEB_ROOT = resolve(import.meta.dirname, '..');
const SRC = join(WEB_ROOT, 'src');
const DIST = join(WEB_ROOT, 'dist', 'fiance');

const CLASS_ALLOWLIST = new Set(['ng-star-inserted', 'lucide', 'lucide-icon']);

function walk(dir, match, out = []) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      walk(full, match, out);
    } else if (match.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

function toPascalCase(name) {
  return name.replace(
    /(\w)([a-z0-9]*)(_|-|\s*)/g,
    (_all, head, tail) => head.toUpperCase() + tail.toLowerCase()
  );
}

function registeredIcons(tsFiles) {
  const names = new Set();
  let found = false;

  for (const file of tsFiles) {
    const pick = readFileSync(file, 'utf8').match(/LucideAngularModule\.pick\(\{([\s\S]*?)\}\)/);
    if (!pick) continue;
    found = true;
    for (const raw of pick[1].split(',')) {
      const name = raw
        .trim()
        .replace(/\/\/.*$/, '')
        .trim();
      if (name) names.add(name);
    }
  }

  if (!found) {
    throw new Error('Não encontrei LucideAngularModule.pick({...}) em nenhum arquivo de src/.');
  }
  return names;
}

function usedIcons(files) {
  const found = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    for (const match of source.matchAll(/<lucide-icon\b[^>]*?\sname="([a-z0-9-]+)"/g)) {
      found.push({ file, name: match[1] });
    }

    for (const binding of source.matchAll(/\[name\]="([^"]*)"/g)) {
      const results = binding[1].replace(/[!=]==?\s*'[^']*'/g, '');
      for (const literal of results.matchAll(/'([a-z][a-z0-9-]*)'/g)) {
        found.push({ file, name: literal[1] });
      }
    }

    for (const match of source.matchAll(/\bicon:\s*'([a-z][a-z0-9-]*)'/g)) {
      found.push({ file, name: match[1] });
    }
  }

  return found;
}

function classesFromCss(css, into = new Set()) {
  for (const match of css.matchAll(/\.((?:[\w-]|\\.)+)/g)) {
    into.add(match[1].replace(/\\(.)/g, '$1'));
  }
  return into;
}

function inlineStyleClasses(files, into = new Set()) {
  for (const file of files) {
    for (const literal of readFileSync(file, 'utf8').matchAll(/`([^`]*)`/g)) {
      if (/[.#:[][^;{}]*\{/.test(literal[1])) classesFromCss(literal[1], into);
    }
  }
  return into;
}

function knownClasses(tsFiles) {
  const built = walk(DIST, /\.css$/);
  if (built.length === 0) {
    throw new Error(
      `Nenhum CSS em ${relative(WEB_ROOT, DIST)}. Rode "npm run build" antes de "npm run lint:ui".`
    );
  }

  const classes = new Set(CLASS_ALLOWLIST);
  for (const file of [...built, ...walk(SRC, /\.(css|scss)$/)]) {
    classesFromCss(readFileSync(file, 'utf8'), classes);
  }
  inlineStyleClasses(tsFiles, classes);
  return classes;
}

function usedClasses(files) {
  const found = [];

  const push = (file, raw) => {
    for (const token of raw.split(/\s+/)) {
      const clean = token.trim();
      if (!clean || clean.includes('{{') || clean.includes('$')) continue;
      found.push({ file, name: clean });
    }
  };

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    for (const match of source.matchAll(/\sclass="([^"{}]*)"/g)) {
      push(file, match[1]);
    }

    for (const match of source.matchAll(/\[class\.([\w-]+)\]/g)) {
      found.push({ file, name: match[1] });
    }

    for (const binding of source.matchAll(/\[(?:ngClass|class)\]="([^"]*)"/g)) {
      for (const literal of binding[1].matchAll(/'([^']*)'/g)) {
        push(file, literal[1]);
      }
    }
  }

  return found;
}

const JUDGMENT_TERMS = [
  'verdict',
  'fair_price',
  'score',
  'margin_of_safety',
  'dip_score',
  'recommendation',
];

const EXPLAINERS = [
  'app-provenance',
  'app-help-tooltip',
  'app-metric-with-context',
  'app-score-ruler',
  'app-margin-of-safety',
  'app-insight',
  'app-ruler-track',
  '<details',
];

const OPT_OUT = /<!--\s*sem-explicabilidade:\s*\S[^>]*-->/;

function rendersJudgment(source) {
  const dynamic = [
    ...source.matchAll(/\{\{([^}]*)\}\}/g),
    ...source.matchAll(/\[[\w.-]+\]="([^"]*)"/g),
    ...source.matchAll(/@(?:if|for)\s*\(([^)]*)\)/g),
  ].map(match => match[1]);

  return dynamic.some(expr => JUDGMENT_TERMS.some(term => expr.includes(term)));
}

function missingExplainers(htmlFiles) {
  const problems = [];

  for (const file of htmlFiles) {
    const source = readFileSync(file, 'utf8');
    if (!rendersJudgment(source)) continue;
    if (OPT_OUT.test(source)) continue;
    if (EXPLAINERS.some(marker => source.includes(marker))) continue;

    problems.push({ file, name: relative(WEB_ROOT, file) });
  }

  return problems;
}

function missingChartAlternatives(files) {
  const problems = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    const desenhaDado = /<svg[\s\S]*?@for[\s\S]*?<\/svg>/.test(source);
    if (!desenhaDado) continue;

    if (/<table/.test(source)) continue;

    problems.push({ file, name: relative(WEB_ROOT, file) });
  }

  return problems;
}

function missingAccessibleNames(files) {
  const problems = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    for (const match of source.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g)) {
      const [, attrs, body] = match;
      if (/aria-label|aria-labelledby/.test(attrs)) continue;

      const semTags = body.replace(/<[^>]+>/g, ' ');
      if (/[A-Za-zÀ-ÿ]{2,}/.test(semTags)) continue;

      problems.push({
        file,
        name: `${relative(WEB_ROOT, file)}: ${body.trim().slice(0, 48).replace(/\s+/g, ' ')}`,
      });
    }
  }

  return problems;
}

const PROJECTED_FIELDS = ['portfolio_value', 'passive_income_monthly'];

function projectionsWithoutBand(files) {
  const problems = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    for (const field of PROJECTED_FIELDS) {
      const usaBase = new RegExp(String.raw`\.${field}(?!_)`).test(source);
      if (!usaBase) continue;
      if (source.includes(`${field}_low`) && source.includes(`${field}_high`)) continue;

      problems.push({ file, name: `${relative(WEB_ROOT, file)}: ${field} sem faixa` });
    }
  }

  return problems;
}

const CERTEZA = [
  /\bvai\s+(subir|cair|render|valorizar|desvalorizar)\b/gi,
  /\bcertamente\b/gi,
  /\bcom\s+certeza\b/gi,
  /\bgarantid[oa]s?\b/gi,
  /\bgarante\s+(retorno|lucro|rendimento)\b/gi,
  /\blucro\s+cert[oa]\b/gi,
  /\bsem\s+risco\b/gi,
  /\bsempre\s+(sobe|cai|rende)\b/gi,
  /\bnunca\s+(cai|perde)\b/gi,
];

const NEGACAO = /\b(n[ãa]o|nem|sem|jamais)\b[^.;]{0,24}$/i;

function certaintyLanguage(files) {
  const problems = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    for (const padrao of CERTEZA) {
      padrao.lastIndex = 0;
      for (const match of source.matchAll(padrao)) {
        const antes = source.slice(Math.max(0, match.index - 60), match.index);
        if (NEGACAO.test(antes.replace(/\s+/g, ' '))) continue;

        const trecho = source
          .slice(Math.max(0, match.index - 30), match.index + match[0].length + 20)
          .replace(/\s+/g, ' ')
          .trim();
        problems.push({ file, name: `${relative(WEB_ROOT, file)}: …${trecho}…` });
      }
    }
  }

  return problems;
}

/**
 * Tipografia fora da escala de papéis.
 *
 * A escala é por papel, não por tamanho: `fi-body`, `fi-caption`, `fi-label`,
 * `fi-metric`, `fi-verdict`. Escrever `text-sm font-medium` no template reabre
 * a decisão a cada tela — e foi assim que o produto acabou com 384 utilitárias
 * de tamanho convivendo com 372 papéis, dando dois corpos diferentes para a
 * mesma coisa em telas vizinhas.
 *
 * É também onde "serifa decide, sans mede" se sustenta: o papel diz qual
 * família usar, o utilitário de tamanho não diz nada.
 */
const TIPO_CRU =
  /\b(?:text-(?:xs|sm|base|lg|xl|[2-9]xl)|font-(?:thin|extralight|light|normal|medium|semibold|bold|extrabold|black))\b/g;

function tipografiaCrua(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    for (const match of source.matchAll(/\sclass="([^"{}]*)"/g)) {
      for (const cru of match[1].matchAll(TIPO_CRU)) {
        problems.push({ file, name: `${relative(WEB_ROOT, file)}: ${cru[0]}` });
      }
    }
  }
  return problems;
}

/**
 * Raio fora do repertório, ou raio grande no que não flutua.
 *
 * São quatro raios: `sm` para marca dentro de instrumento, `md` para tudo que
 * está assentado no chão, `lg` só para o que flutua por cima da página, e
 * `pill`. `rounded-xl` e `rounded-full` são do Tailwind, não dos tokens — e o
 * produto chegou a ter três raios diferentes para a mesma caixa.
 *
 * O que separa "flutua" de "assentado" é a sombra: só quem flutua tem uma.
 */
function raioForaDaEscala(files) {
  const problems = [];
  for (const file of files) {
    for (const [n, line] of readFileSync(file, 'utf8').split('\n').entries()) {
      for (const match of line.matchAll(/\brounded-(?:xl|[2-9]xl|full)\b/g)) {
        problems.push({ file, name: `${relative(WEB_ROOT, file)}:${n + 1}: ${match[0]}` });
      }
      if (/\brounded-lg\b/.test(line) && !/shadow-(?:popover|drawer)/.test(line)) {
        problems.push({
          file,
          name: `${relative(WEB_ROOT, file)}:${n + 1}: rounded-lg sem sombra`,
        });
      }
    }
  }
  return problems;
}

/**
 * Dois sistemas de foco no mesmo produto.
 *
 * O anel de foco é `outline` na cor da marca, com a espessura e o afastamento
 * dos tokens, e vem de graça em `.input`, `.btn-*` e `.fi-focusable`. O
 * `focus:ring` do Tailwind desenha outra coisa — e `focus:outline-none` sem
 * substituto apaga o foco por inteiro, que é o pior dos casos.
 */
function focoConcorrente(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    for (const match of source.matchAll(/\bfocus:(?:ring[\w/-]*|outline-none)\b/g)) {
      problems.push({ file, name: `${relative(WEB_ROOT, file)}: ${match[0]}` });
    }
  }
  return problems;
}

/**
 * Controle montado à mão.
 *
 * `.btn-primary`, `.btn-secondary`, `.btn-icon`, `.btn-link`, `.btn-quiet`,
 * `.menu-item` e `.input` existem. Remontar um deles com utilitárias produz um
 * alvo de toque, um raio e um foco diferentes a cada tela — foi o que
 * aconteceu: nove grafias de botão só de ícone, com cinco alturas.
 *
 * Ficam de fora os controles que o navegador desenha sozinho (caixa de
 * seleção, rádio, faixa, arquivo) e o arquivo que declara o motivo por escrito.
 */
const CLASSES_DE_CONTROLE = [
  'btn-primary',
  'btn-secondary',
  'btn-icon',
  'btn-link',
  'btn-quiet',
  'menu-item',
  'pagination-btn',
  'subtab-btn',
  'th-sort',
  'nav-link',
  'verdict-pill',
  'input',
  'range-slider',
  'input-bare',
];
const TIPOS_NATIVOS = /type="(?:checkbox|radio|range|file|hidden)"/;
const ESCAPE_CONTROLE = /<!--\s*controle-proprio:\s*\S/;

function controleForaDoSistema(files) {
  const problems = [];
  for (const file of files) {
    const bruto = readFileSync(file, 'utf8');
    if (ESCAPE_CONTROLE.test(bruto)) continue;
    // `<select>` citado num comentário de documentação não é um controle.
    const source = bruto.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

    for (const match of source.matchAll(/<(button|input|select|textarea)\b([^>]*)>/g)) {
      const [, tag, attrs] = match;
      if (TIPOS_NATIVOS.test(attrs)) continue;
      const classe = attrs.match(/\sclass="([^"]*)"/)?.[1] ?? '';
      if (CLASSES_DE_CONTROLE.some(c => new RegExp(`\\b${c}\\b`).test(classe))) continue;
      problems.push({
        file,
        name: `${relative(WEB_ROOT, file)}: <${tag}> sem classe do sistema`,
      });
    }
  }
  return problems;
}

/**
 * Ícone decorando um título.
 *
 * Um ícone ao lado de "Lançamentos" não acrescenta informação: ele faz cada
 * seção parecer o cabeçalho de um card de painel. Onde o ícone é o dado — o
 * estado de um diagnóstico, o cadeado de um recurso fechado — ele fica, e a
 * checagem pula esses arquivos por nome.
 */
function iconeDecorativoEmTitulo(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    for (const match of source.matchAll(/<(h[1-4])\b[^>]*>([\s\S]*?)<\/\1>/g)) {
      if (!/<lucide-icon\b[^>]*name="[a-z0-9-]+"/.test(match[2])) continue;
      problems.push({ file, name: `${relative(WEB_ROOT, file)}: <${match[1]}> com ícone` });
    }
  }
  return problems;
}

function report(title, problems, hint) {
  if (problems.length === 0) return 0;

  console.error(`\n✗ ${title}`);
  const byName = new Map();
  for (const problem of problems) {
    const list = byName.get(problem.name) ?? [];
    list.push(relative(WEB_ROOT, problem.file));
    byName.set(problem.name, list);
  }
  for (const [name, files] of [...byName].sort()) {
    const onde = [...new Set(files)].filter(caminho => caminho !== name);
    console.error(onde.length ? `  ${name}  —  ${onde.join(', ')}` : `  ${name}`);
  }
  console.error(`  ${hint}`);
  return byName.size;
}

/** Onde o ícone do título é o próprio dado, e não decoração. */
const TITULO_COM_ICONE_LEGITIMO = [
  'dip-diagnosis.component.ts',
  'empty-state.component.ts',
  'gate.component.ts',
];

function main() {
  const templates = [...walk(SRC, /\.html$/), ...walk(SRC, /\.ts$/)].filter(
    file => !file.endsWith('.spec.ts')
  );

  const tsFiles = templates.filter(file => file.endsWith('.ts'));
  const registered = registeredIcons(tsFiles);
  const missingIcons = usedIcons(templates).filter(use => !registered.has(toPascalCase(use.name)));

  const known = knownClasses(tsFiles);
  const missingClasses = usedClasses(templates).filter(use => !known.has(use.name));

  const semExplicacao = missingExplainers(templates.filter(file => file.endsWith('.html')));
  const semTabela = missingChartAlternatives(templates);
  const semNome = missingAccessibleNames(templates);
  const semFaixa = projectionsWithoutBand(templates);
  const comCerteza = certaintyLanguage(templates.filter(f => f.endsWith('.html')));
  const tipoCru = tipografiaCrua(templates);
  const raioSolto = raioForaDaEscala(templates);
  const focoDuplo = focoConcorrente(templates);
  const controleSolto = controleForaDoSistema(templates);
  const tituloDecorado = iconeDecorativoEmTitulo(
    templates.filter(f => !TITULO_COM_ICONE_LEGITIMO.some(nome => f.endsWith(nome)))
  );

  const problems =
    report(
      'Ícone do Lucide usado sem registro em src/app/app.config.ts',
      missingIcons,
      'Importe o ícone e adicione-o a LucideAngularModule.pick({...}).'
    ) +
    report(
      'Classe CSS usada e não emitida pelo build',
      missingClasses,
      'Ou defina a classe em src/styles.css, ou corrija o nome: papel de cor ' +
        'inexistente faz o Tailwind descartar a utilitária em silêncio.'
    ) +
    report(
      'Tela exibe julgamento sem como conferir a conta',
      semExplicacao,
      'Adicione <app-provenance>, <app-help-tooltip> ou outro explicador. Se a ' +
        'tela realmente não precisa, declare o motivo: ' +
        '<!-- sem-explicabilidade: o número já vem explicado no card pai -->'
    ) +
    report(
      'Gráfico sem alternativa textual',
      semTabela,
      'Adicione uma <table> com a série. aria-label resume, e resumo não é o dado: ' +
        'quem usa leitor de tela precisa comparar ponto a ponto.'
    ) +
    report(
      'Botão sem nome acessível',
      semNome,
      'Adicione aria-label. Sem ele o leitor de tela anuncia só "botão", e a ' +
        'pessoa tem que adivinhar se aquilo apaga a posição ou fecha o modal.'
    ) +
    report(
      'Número projetado exibido sem faixa',
      semFaixa,
      'Mostre piso e teto (os campos _low e _high). Um valor único a cinco anos ' +
        'empresta precisão de centavo a uma pilha de premissas — e é em cima dele ' +
        'que a pessoa decide quanto poupar.'
    ) +
    report(
      'Tela promete o futuro',
      comCerteza,
      'Preço futuro não se afirma. Troque por linguagem condicional, ou negue ' +
        'explicitamente (“não há garantia de retorno” passa; “retorno garantido” não).'
    ) +
    report(
      'Tipografia fora da escala de papéis',
      tipoCru,
      'Use o papel: fi-body, fi-caption, fi-label, fi-title, fi-eyebrow, fi-metric, ' +
        'fi-metric-sm, fi-money-lg, fi-money-xl, fi-verdict, fi-verdict-sm, fi-ticker. ' +
        'Tamanho solto reabre a decisão a cada tela.'
    ) +
    report(
      'Raio fora da escala, ou raio de flutuante no que está no chão',
      raioSolto,
      'São quatro: rounded-sm (marca), rounded-md (assentado), rounded-lg (só o que ' +
        'flutua, e flutuar é ter sombra) e rounded-pill. rounded-xl e rounded-full são ' +
        'do Tailwind, não dos tokens.'
    ) +
    report(
      'Segundo sistema de foco',
      focoDuplo,
      'O anel de foco é outline na cor da marca, com espessura e afastamento dos ' +
        'tokens, e já vem em .input, .btn-* e .fi-focusable. focus:outline-none sem ' +
        'substituto apaga o foco.'
    ) +
    report(
      'Controle montado à mão',
      controleSolto,
      'Use .btn-primary, .btn-secondary, .btn-icon, .btn-link, .btn-quiet, .menu-item ' +
        'ou .input. Se este controle é mesmo único, declare o motivo no arquivo: ' +
        '<!-- controle-proprio: ... -->'
    ) +
    report(
      'Ícone decorando título',
      tituloDecorado,
      'Tire o ícone do <h*>. Ao lado de um título ele não acrescenta informação — ' +
        'faz a seção parecer cabeçalho de card de painel.'
    );

  if (problems > 0) {
    console.error(`\n${problems} problema(s) que quebram a tela sem quebrar o build.\n`);
    process.exit(1);
  }

  console.log(
    '✓ Ícones, classes, explicabilidade, gráficos, nomes, faixas, linguagem, ' +
      'tipografia, raio, foco, controles e títulos conferidos.'
  );
}

main();
