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

function camadaForaDaEscala(files) {
  const problems = [];
  for (const file of files) {
    for (const [n, line] of readFileSync(file, 'utf8').split('\n').entries()) {
      for (const match of line.matchAll(/z-\[[^\]]+\]/g)) {
        problems.push({ file, name: `${relative(WEB_ROOT, file)}:${n + 1}: ${match[0]}` });
      }
    }
  }
  return problems;
}

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

function rotaSemTitulo(files) {
  const rotas = files.filter(f => f.endsWith('app.routes.ts'));
  if (rotas.length === 0) return [];

  const fonte = readFileSync(rotas[0], 'utf8');
  const alvos = new Set();
  for (const match of fonte.matchAll(/import\('([^']+)'\)/g)) {
    alvos.add(match[1].replace(/^\.\//, ''));
  }

  const problems = [];
  for (const alvo of [...alvos].sort()) {
    const ts = join(SRC, 'app', `${alvo}.ts`);
    let source;
    try {
      source = readFileSync(ts, 'utf8');
    } catch {
      continue;
    }
    const url = source.match(/templateUrl:\s*'([^']+)'/);
    if (url) {
      try {
        source += readFileSync(join(ts, '..', url[1]), 'utf8');
      } catch {}
    }

    if (/<router-outlet/.test(source)) continue;

    const n =
      (source.match(/<h1\b/g) ?? []).length + (source.match(/<app-page-header\b/g) ?? []).length;
    if (n === 1) continue;
    problems.push({
      file: ts,
      name: `${alvo}: ${n === 0 ? 'nenhum <h1>' : `${n} títulos de tela`}`,
    });
  }
  return problems;
}

const SERIFA = /\bfi-verdict(?:-sm)?\b/;
const ESCAPE_VEREDITO = /<!--\s*veredito:\s*\S/;

const CIFRA = /\{\{[^}]*\|\s*(?:number|currency|percent)\b|R\$/;

function conteudoDe(source, tag, aberturaFim) {
  const marca = new RegExp(`<(/?)${tag}\\b`, 'g');
  marca.lastIndex = aberturaFim;
  let nivel = 1;
  let m;
  while ((m = marca.exec(source)) !== null) {
    nivel += m[1] === '/' ? -1 : 1;
    if (nivel === 0) return source.slice(aberturaFim, m.index);
  }
  return source.slice(aberturaFim);
}

function serifaForaDeConclusao(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    const nome = relative(WEB_ROOT, file);
    const temEscape = ESCAPE_VEREDITO.test(source);

    for (const abertura of source.matchAll(/<(h[1-6]|p|div|span)\b([^>]*)>/g)) {
      const [bruto, tag, attrs] = abertura;
      if (!SERIFA.test(attrs)) continue;

      const fim = abertura.index + bruto.length;
      const texto = conteudoDe(source, tag, fim).replace(/<[^>]*>/g, ' ');

      if (CIFRA.test(texto)) {
        problems.push({ file, name: `${nome}: <${tag}> com cifra em serifa` });
        continue;
      }
      if (/^h[1-4]$/.test(tag) && !temEscape) {
        problems.push({ file, name: `${nome}: <${tag}> em serifa` });
      }
    }
  }
  return problems;
}

function ordemDeCabecalho(files) {
  const problems = [];
  for (const file of files) {
    const niveis = [...readFileSync(file, 'utf8').matchAll(/<h([1-6])\b/g)].map(m => Number(m[1]));
    let anterior = 0;
    for (const nivel of niveis) {
      if (anterior && nivel > anterior + 1) {
        problems.push({
          file,
          name: `${relative(WEB_ROOT, file)}: <h${anterior}> seguido de <h${nivel}>`,
        });
        break;
      }
      anterior = nivel;
    }
  }
  return problems;
}

const ESCAPE_CAMADA_LOCAL = /<!--\s*camada-local:\s*\S/;

function camadaNumerica(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    if (ESCAPE_CAMADA_LOCAL.test(source)) continue;
    for (const [n, line] of source.split('\n').entries()) {
      for (const match of line.matchAll(/(?:^|["'\s])(z-\d+)\b/g)) {
        problems.push({ file, name: `${relative(WEB_ROOT, file)}:${n + 1}: ${match[1]}` });
      }
    }
  }
  return problems;
}

const ESCAPE_CAIXA = /<!--\s*caixa-propria:\s*\S/;

function caixaMontadaAMao(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    if (ESCAPE_CAIXA.test(source)) continue;
    for (const match of source.matchAll(/\sclass="([^"{}]*)"/g)) {
      const classes = match[1];

      if (!/\brounded-md\b/.test(classes)) continue;
      if (!/\bborder-hairline\b/.test(classes)) continue;
      if (/\b(?:absolute|fixed|shadow-\w+)\b/.test(classes)) continue;

      problems.push({
        file,
        name: `${relative(WEB_ROOT, file)}: ${classes.trim().slice(0, 56)}`,
      });
    }
  }
  return problems;
}

function esqueletoImprovisado(files) {
  const problems = [];
  for (const file of files) {
    if (file.endsWith('skeleton.component.ts')) continue;
    if (!/\banimate-pulse\b/.test(readFileSync(file, 'utf8'))) continue;
    problems.push({ file, name: `${relative(WEB_ROOT, file)}: animate-pulse` });
  }
  return problems;
}

function direcaoForaDeTabela(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    for (const match of source.matchAll(/\btext-(?:up|down)\b/g)) {
      const antes = source.slice(0, match.index);

      if (antes.lastIndexOf('<td') > antes.lastIndexOf('</td>')) continue;

      const linha = antes.split('\n').length;
      problems.push({ file, name: `${relative(WEB_ROOT, file)}:${linha}` });
    }
  }
  return problems;
}

function desabilitadoSemMotivo(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    for (const match of source.matchAll(/<button\b([\s\S]{0,600}?)<\/button>/g)) {
      const bloco = match[1];
      if (!/\[disabled\]|(?:^|\s)disabled(?:[\s>=])/.test(bloco)) continue;
      if (/\[title\]|title="|aria-describedby|\[attr\.title\]/.test(bloco)) continue;

      if (/\{\{[^}]*\?[^}]*'/.test(bloco)) continue;

      const rotulo = bloco
        .replace(/<[^>]*>/g, ' ')
        .trim()
        .replace(/\s+/g, ' ')
        .slice(0, 40);
      problems.push({ file, name: `${relative(WEB_ROOT, file)}: ${rotulo || '<button>'}` });
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
  const camadaSolta = camadaForaDaEscala(templates);
  const focoDuplo = focoConcorrente(templates);
  const controleSolto = controleForaDoSistema(templates);
  const tituloDecorado = iconeDecorativoEmTitulo(
    templates.filter(f => !TITULO_COM_ICONE_LEGITIMO.some(nome => f.endsWith(nome)))
  );
  const semTitulo = rotaSemTitulo(templates);
  const serifaSolta = serifaForaDeConclusao(templates);
  const cabecalhoTorto = ordemDeCabecalho(templates);
  const camadaNumerada = camadaNumerica(templates);
  const caixaSolta = caixaMontadaAMao(templates);
  const esqueletoSolto = esqueletoImprovisado(templates);
  const direcaoSolta = direcaoForaDeTabela(templates);
  const becoSemSaida = desabilitadoSemMotivo(templates);

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
      'Camada escrita como número',
      camadaSolta,
      'Use o nome da camada: z-nav, z-drawer, z-drawer-panel, z-sheet, z-popover, ' +
        'z-loader, z-toast. Número solto reabre a ordem de empilhamento a cada tela — ' +
        'foi assim que o loader foi parar atrás dos modais.'
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
    ) +
    report(
      'Rota sem nome de tela',
      semTitulo,
      'Cada rota precisa de exatamente um <h1>, normalmente via <app-page-header>. ' +
        'Sem ele a tela não diz onde a pessoa está, e a hierarquia de cabeçalho ' +
        'começa no meio.'
    ) +
    report(
      'Serifa fora de conclusão',
      serifaSolta,
      'fi-verdict carrega conclusão do sistema, não título nem número. Título é ' +
        'fi-title; cifra é fi-metric ou fi-money-* (fi-verdict não tem cifra ' +
        'tabular). Cabeçalho que é mesmo uma conclusão declara o motivo: ' +
        '<!-- veredito: o veredito de saúde da carteira -->'
    ) +
    report(
      'Cabeçalho fora de ordem',
      cabecalhoTorto,
      'Não pule nível: depois de <h2> vem <h2> ou <h3>, nunca <h4>. É assim que ' +
        'quem usa leitor de tela varre a página.'
    ) +
    report(
      'Controle desabilitado sem motivo',
      becoSemSaida,
      'Diga por que não dá para clicar: title, aria-describedby, ou um rótulo ' +
        'que mude com o estado. Opacidade a 50% sozinha é um beco sem saída.'
    ) +
    report(
      'Caixa montada à mão',
      caixaSolta,
      'Escolha o papel: .card para objeto com que se age, .notice para aviso, ' +
        '.fi-block para seção. Moldura de tabela de gráfico é um fio, não uma ' +
        'caixa. Se esta caixa é mesmo única: <!-- caixa-propria: ... -->'
    ) +
    report(
      'Esqueleto improvisado',
      esqueletoSolto,
      'Use <app-skeleton shape="...">. Retângulo genérico faz a página saltar ' +
        'quando o dado chega, e dá a carregar uma aparência por tela.'
    ) +
    report(
      'Cor de direção fora de coluna de tabela',
      direcaoSolta,
      'O sinal e a palavra já dizem que subiu ou caiu. text-up e text-down ' +
        'sobrevivem só em <td>, onde se varre trinta linhas de relance — em ' +
        'título, frase e card eles roubam a cor que pertence ao julgamento.'
    ) +
    report(
      'Camada escrita como número do Tailwind',
      camadaNumerada,
      'Use o nome da camada: z-popover, z-drawer, z-sheet, z-nav. z-10 e z-50 ' +
        'ficam abaixo de z-nav (100) e mandam o popover para trás do cabeçalho. ' +
        'Camada local de tabela declara o motivo: <!-- camada-local: ... -->'
    );

  if (problems > 0) {
    console.error(`\n${problems} problema(s) que quebram a tela sem quebrar o build.\n`);
    process.exit(1);
  }

  console.log(
    '✓ Ícones, classes, explicabilidade, gráficos, nomes, faixas, linguagem, ' +
      'tipografia, raio, camada, foco, controles, títulos, nome de tela, serifa, ' +
      'ordem de cabeçalho, camada numérica, caixa, esqueleto, direção e ' +
      'estado desabilitado conferidos.'
  );
}

main();
