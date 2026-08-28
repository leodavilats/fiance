#!/usr/bin/env node
/**
 * Lint das duas coisas que quebram a tela sem quebrar o build.
 *
 * 1. **Ícone do Lucide não registrado.** `LucideAngularModule.pick({...})` é
 *    manual. Nome ausente ou errado compila e só falha em runtime, com
 *    `The "x" icon has not been provided`. Já aconteceu.
 *
 * 2. **Classe CSS que não existe.** Já aconteceu com `.card`, `.btn-primary`,
 *    `.tag`, `.verdict-pill`, `verdict-*` e `bg-success`. A fonte de verdade
 *    aqui não é uma lista escrita à mão: é o CSS que o build realmente emitiu.
 *    Se a classe não está lá, ou o Tailwind não a reconheceu (papel de cor
 *    inexistente) ou ninguém a definiu — e nos dois casos a tela fica sem
 *    estilo em silêncio.
 *
 * 3. **Julgamento exibido sem como conferir a conta.** Score, veredito, preço
 *    justo e sugestão são opinião do sistema sobre o dinheiro de alguém.
 *    Opinião sem método à vista é fé, e essa regra escrita só na documentação
 *    se perde na terceira tela nova.
 *
 * Uso: `node tools/lint-ui.mjs` depois de `npm run build`.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';

const WEB_ROOT = resolve(import.meta.dirname, '..');
const SRC = join(WEB_ROOT, 'src');
const DIST = join(WEB_ROOT, 'dist', 'fiance');

/** Classes aplicadas por JS ou por bibliotecas, que não passam pelo scanner. */
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

/**
 * A mesma transformação que `LucideAngularComponent.toPascalCase` faz antes de
 * procurar a chave no objeto do `pick`. Reimplementar o kebab ao contrário daria
 * respostas erradas em nomes com dígito: `trash2` e `trash-2` resolvem os dois
 * para `Trash2`, e um lint que não soubesse disso reprovaria código que funciona.
 */
function toPascalCase(name) {
  return name.replace(
    /(\w)([a-z0-9]*)(_|-|\s*)/g,
    (_all, head, tail) => head.toUpperCase() + tail.toLowerCase()
  );
}

// --------------------------------------------------------------------------
// 1. Ícones
// --------------------------------------------------------------------------

/**
 * O registro é procurado onde ele estiver, e não num caminho fixo: ele já mudou
 * de `main.ts` para `app.config.ts` quando a renderização no servidor entrou, e
 * um lint que quebra ao mover arquivo acaba desligado.
 */
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

/**
 * Nomes usados. Três formas cobrem o uso real do repo: atributo estático,
 * literal dentro de um binding `[name]`, e a chave `icon:` de um objeto de
 * configuração (é assim que a navegação e a busca global declaram o ícone).
 */
function usedIcons(files) {
  const found = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    for (const match of source.matchAll(/<lucide-icon\b[^>]*?\sname="([a-z0-9-]+)"/g)) {
      found.push({ file, name: match[1] });
    }

    for (const binding of source.matchAll(/\[name\]="([^"]*)"/g)) {
      // Num ternário, o literal comparado não é nome de ícone — em
      // `type === 'error' ? 'circle-x' : 'info'` só os dois últimos são.
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

// --------------------------------------------------------------------------
// 2. Classes
// --------------------------------------------------------------------------

/** Seletores de classe de um texto CSS, desfazendo os escapes do Tailwind. */
function classesFromCss(css, into = new Set()) {
  // `\.` cobre `w-1\/2` e `bg-brand\/20`, que o Tailwind emite escapados.
  for (const match of css.matchAll(/\.((?:[\w-]|\\.)+)/g)) {
    into.add(match[1].replace(/\\(.)/g, '$1'));
  }
  return into;
}

/**
 * Classes definidas em estilo inline de componente.
 *
 * O Angular embute o CSS do componente no bundle JS, não no `.css` — então o
 * arquivo emitido não as contém e elas precisam vir da fonte. Um literal de
 * crase só é tratado como CSS se tiver bloco de declaração; assim o template
 * inline, que também é literal de crase, fica de fora.
 */
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

/** Tokens de classe escritos no template, incluindo os de `[class.x]` e `ngClass`. */
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

    // `[ngClass]` e `[class]` com objeto ou ternário: só os literais.
    for (const binding of source.matchAll(/\[(?:ngClass|class)\]="([^"]*)"/g)) {
      for (const literal of binding[1].matchAll(/'([^']*)'/g)) {
        push(file, literal[1]);
      }
    }
  }

  return found;
}

// --------------------------------------------------------------------------
// 3. Explicabilidade
// --------------------------------------------------------------------------

/**
 * Todo julgamento **renderizado** precisa de uma forma de conferir a conta.
 *
 * A regra é de produto: score, veredito, preço justo e sugestão são opinião do
 * sistema sobre o dinheiro de alguém, e opinião sem método à vista é fé. Vira
 * regra de código porque, escrita só na documentação, ela se perde na terceira
 * tela nova — foi o que aconteceu com três campos calculados que nunca
 * chegaram ao cliente.
 *
 * A detecção olha o que é **interpolado ou vinculado**, não o que aparece em
 * prosa: a tela de preferências fala sobre o score sem exibir nenhum, e
 * reprová-la ensinaria a ignorar o lint.
 */
const JUDGMENT_TERMS = [
  'verdict',
  'fair_price',
  'score',
  'margin_of_safety',
  'dip_score',
  'recommendation',
];

/** O que conta como "dá para conferir": painel, tooltip, régua ou `<details>`. */
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

/** Escape declarado, com motivo obrigatório. Sem motivo, não é escape. */
const OPT_OUT = /<!--\s*sem-explicabilidade:\s*\S[^>]*-->/;

function rendersJudgment(source) {
  // Interpolação `{{ ... }}` e binding `[x]="..."` / `@if (...)`.
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

// --------------------------------------------------------------------------
// 4. Alternativa textual de gráfico
// --------------------------------------------------------------------------

/**
 * Todo SVG que desenha dado precisa de uma forma de ler o dado sem enxergá-lo.
 *
 * `aria-label` resume — "a carteira foi de 3% a 11%" — e resumo não é o dado.
 * A alternativa que serve é a tabela: quem usa leitor de tela compara ponto a
 * ponto, e quem enxerga também quer o número exato de vez em quando.
 *
 * Ícone não conta como gráfico: ele é decoração, e exigir tabela dele
 * transformaria a regra em ruído que se aprende a ignorar.
 */
function missingChartAlternatives(files) {
  const problems = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    // `<svg` com `<path`/`<line`/`<circle` gerado em laço é gráfico de dado;
    // ícone é um `<svg>` estático, e o Lucide nem chega ao template.
    const desenhaDado = /<svg[\s\S]*?@for[\s\S]*?<\/svg>/.test(source);
    if (!desenhaDado) continue;

    if (/<table/.test(source)) continue;

    problems.push({ file, name: relative(WEB_ROOT, file) });
  }

  return problems;
}

// --------------------------------------------------------------------------
// 5. Nome acessível
// --------------------------------------------------------------------------

/**
 * Botão só com ícone precisa dizer o que faz.
 *
 * Sem nome acessível, o leitor de tela anuncia "botão" — e a pessoa tem que
 * adivinhar se aquilo apaga a posição ou fecha o modal. O ícone comunica para
 * quem enxerga; o `aria-label` comunica para o resto.
 *
 * A checagem é por ausência de **texto**: um botão com palavra dentro já se
 * anuncia sozinho e não precisa de rótulo — repetir ali seria ruído duplicado
 * no leitor de tela.
 */
function missingAccessibleNames(files) {
  const problems = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');

    for (const match of source.matchAll(/<button([^>]*)>([\s\S]*?)<\/button>/g)) {
      const [, attrs, body] = match;
      if (/aria-label|aria-labelledby/.test(attrs)) continue;

      // Texto visível, incluindo o que vem de interpolação.
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

// --------------------------------------------------------------------------

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

function main() {
  // Fixture de teste não é tela: ela existe para exercitar um componente, e
  // cobrar dela ícone registrado ou classe emitida produz falso positivo — que
  // é como um lint acaba desligado.
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

  const problems =
    report(
      'Ícone do Lucide usado sem registro em src/main.ts',
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
    );

  if (problems > 0) {
    console.error(`\n${problems} problema(s) que quebram a tela sem quebrar o build.\n`);
    process.exit(1);
  }

  console.log('✓ Ícones, classes, explicabilidade, gráficos e nomes acessíveis conferidos.');
}

main();
