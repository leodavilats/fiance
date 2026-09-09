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

/**
 * A forma única de escapar de uma regra: a regra pelo nome, e o motivo escrito.
 *
 * Eram cinco grafias diferentes (`sem-explicabilidade`, `controle-proprio`, `caixa-propria`,
 * `camada-local`, `veredito`) para a mesma ideia. Nomear a regra mantém o escape estreito —
 * escapar de cabeçalho não escapa de contraste — e exigir o motivo mantém a exceção visível.
 * O objetivo nunca foi impedir exceções; é impedir exceção invisível.
 */
const DESIGN_EXCEPTION = /<!--\s*design-exception:\s*([a-z-]+)\s*(?:—|-{1,2})\s*\S[^>]*-->/g;

const escapeDe = regra => ({
  test: texto => {
    for (const [, nome] of texto.matchAll(DESIGN_EXCEPTION)) if (nome === regra) return true;
    return false;
  },
});

const OPT_OUT = escapeDe('explicabilidade');

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

/*
 * A parte mecânica de docs/design/AI-TELLS.md.
 *
 * Aquele documento se declara não-checável por máquina, e para composição e redação isso é
 * verdade. A **lista de vocabulário proibido** não é: são frases literais. Nada a conferia, e o
 * custo apareceu — a primeira tela do aplicativo móvel abria com "tudo em um só assistente", que
 * são dois itens da lista numa frase só, e três telas do web decidiam a cor de uma mensagem por
 * um prefixo de glifo, com o símbolo carregando o estado que é papel de cor.
 *
 * Só o que é inequívoco entra. Nada de julgamento sobre hierarquia, simetria ou "parece
 * plausível demais": isso é revisão humana e continua sendo.
 */
const VOCABULARIO_PROIBIDO = [
  [/\brevolucion[áa]ri[oa]s?\b/gi, 'marketing genérico'],
  [/\bsimples\s+e\s+poderos[oa]\b/gi, 'marketing genérico'],
  [/\btudo\s+em\s+um\s+s[óo]\s+\w+/gi, 'marketing genérico'],
  [/\bpr[óo]ximo\s+n[íi]vel\b/gi, 'marketing genérico'],
  [/\btransforme\s+sua\s+rela[çc][ãa]o\b/gi, 'marketing genérico'],
  [/\bcomo\s+posso\s+(?:te\s+)?ajudar\b/gi, 'fala de assistente'],
  [/\bfico\s+feliz\s+em\s+ajudar\b/gi, 'fala de assistente'],
  [/\b[ée]\s+importante\s+notar\b/gi, 'fala de assistente'],
  [/\bn[óo]s\s+entendemos\s+que\b/gi, 'fala de assistente'],
  [/\bassistente\s+(?:financeiro|de\s+investimentos)\b/gi, 'persona de chatbot'],
  [/\bparab[ée]ns\b/gi, 'o produto descreve, não comemora'],
];

/*
 * Pictograma, emoticon, bandeira e os dingbats que já foram usados aqui para carregar estado.
 * Estado é papel de cor; ícone é o Lucide registrado.
 *
 * A faixa de setas fica **fora** de propósito: a seta é a informação em "condição → veredito" e
 * no rótulo de tendência lateral. Seta decorando rótulo de link é revisão humana.
 */
const EMOJI_EM_TEXTO =
  /[\u{1F300}-\u{1FAFF}\u{1F000}-\u{1F0FF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{1F1E6}-\u{1F1FF}]/gu;

const escapeDeVocabulario = escapeDe('vocabulario');

/** Só o que vai para a tela: o literal de `template:`, não comentário nem nome de símbolo. */
function textoDeTemplate(source) {
  const inicio = source.indexOf('template: `');
  if (inicio < 0) return '';
  const abre = inicio + 'template: `'.length;
  const fecha = source.indexOf('`,', abre);
  return source.slice(abre, fecha < 0 ? source.length : fecha);
}

function vocabularioDeIA(files) {
  const problems = [];

  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    if (escapeDeVocabulario.test(source)) continue;

    const template = textoDeTemplate(source);
    if (!template) continue;

    for (const [padrao, motivo] of VOCABULARIO_PROIBIDO) {
      padrao.lastIndex = 0;
      for (const match of template.matchAll(padrao)) {
        problems.push({
          file,
          name: `${relative(WEB_ROOT, file)}: "${match[0]}" — ${motivo}`,
        });
      }
    }

    EMOJI_EM_TEXTO.lastIndex = 0;
    const glifos = [...new Set([...template.matchAll(EMOJI_EM_TEXTO)].map(m => m[0]))];
    if (glifos.length > 0) {
      problems.push({
        file,
        name: `${relative(WEB_ROOT, file)}: ${glifos.join(' ')} em texto de interface`,
      });
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

function contornoDeSeparador(arquivosCss) {
  const problems = [];
  const ABRE_CONTROLE =
    /^\s*\.(?:btn-[a-z-]+|input|input-bare|menu-item|segmented-option|subtab-btn|range-slider|pagination-btn|compact-btn)\b/;

  for (const file of arquivosCss) {
    let dentro = false;
    let seletor = '';

    for (const [n, line] of readFileSync(file, 'utf8').split('\n').entries()) {
      if (ABRE_CONTROLE.test(line)) {
        dentro = true;
        seletor = line;
      } else if (/^\s*[.:*a-z[@]/.test(line) && /[{,]\s*$/.test(line)) {
        dentro = false;
      }
      if (line.trim() === '}') dentro = false;
      if (!dentro) continue;

      /*
       * Controle desabilitado fica de fora: a WCAG 1.4.11 o isenta, e um contorno inerte de
       * baixo croma e justamente o sinal de que nao da para clicar. O que continua cobrado
       * ali e o ROTULO, que o check-contrast.mjs mede em `ink-disabled` a 3:1.
       */
      if (/:disabled/.test(seletor)) continue;

      if (/border(?:-[a-z]+)?(?:-color)?:[^;]*--fi-hairline/.test(line)) {
        problems.push({ file, name: `${relative(WEB_ROOT, file)}:${n + 1}: ${line.trim()}` });
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

/**
 * Camada escrita como número, nas duas grafias.
 *
 * Eram duas regras para a mesma falha: `z-[201]` (valor arbitrário) e `z-50` (escala do
 * Tailwind) erram igual — os dois reabrem a ordem de empilhamento a cada tela, e foi assim que
 * o loader foi parar atrás dos modais. Uma falha, uma regra, uma mensagem.
 */
function camadaForaDaEscala(files) {
  const problems = [];
  for (const file of files) {
    const source = readFileSync(file, 'utf8');
    const escapada = ESCAPE_CAMADA_LOCAL.test(source);
    for (const [n, line] of source.split(/\r?\n/).entries()) {
      for (const match of line.matchAll(/z-\[[^\]]+\]/g)) {
        problems.push({ file, name: `${relative(WEB_ROOT, file)}:${n + 1}: ${match[0]}` });
      }
      if (escapada) continue;
      for (const match of line.matchAll(/(?:^|["'\s])(z-\d+)/g)) {
        problems.push({ file, name: `${relative(WEB_ROOT, file)}:${n + 1}: ${match[1]}` });
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
  'segmented-option',
  'subtab-btn',
  'th-sort',
  'nav-link',
  'verdict-pill',
  'input',
  'range-slider',
  'input-bare',
];
const TIPOS_NATIVOS = /type="(?:checkbox|radio|range|file|hidden)"/;
const ESCAPE_CONTROLE = escapeDe('controle');

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
const ESCAPE_VEREDITO = escapeDe('veredito');

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

const ESCAPE_CAMADA_LOCAL = escapeDe('camada');


const ESCAPE_CAIXA = escapeDe('caixa');

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

/**
 * Aviso, não reprovação.
 *
 * Regra que protege acessibilidade, contrato de produto ou erro silencioso reprova o CI. Regra
 * que protege só preferência visual entra em revisão de código — porque bloquear o CI por gosto
 * gasta a autoridade das regras que valem, e a pessoa passa a ler a lista inteira como ruído.
 */
/*
 * Tela de rota que le dado e nao trata a falha.
 *
 * Quatro das sete secoes de `/patrimonio` renderizavam **nada** quando a leitura falhava: a
 * pagina abria com o titulo e o corpo vazio, e "nao conseguimos ler" ficava indistinguivel de
 * "voce nao tem nada". A loja tinha o booleano da falha e uma tela sozinha o lia.
 *
 * A regra vale so para alvo de rota -- e ali que a pessoa fica presa sem saida. Bloco interno
 * herda o estado do pai.
 */
const LEITURA_DE_DADO = /\.subscribe\(|firstValueFrom|erroDeCarga|loadFailed/;

const TRATA_FALHA = [
  '<app-async-state',
  'role="alert"',
  'notice-adverse',
  'FiErrorState',
];

const ESCAPE_FALHA = escapeDe('falha');

function alvosDeRota() {
  const fonte = join(SRC, 'app', 'app.routes.ts');
  const alvos = new Set();
  try {
    for (const match of readFileSync(fonte, 'utf8').matchAll(/import\('([^']+)'\)/g)) {
      alvos.add(join(SRC, 'app', `${match[1].replace(/^\.\//, '')}.ts`));
    }
  } catch {}
  return alvos;
}

function telaSemTratarFalha(files) {
  const alvos = alvosDeRota();
  const problems = [];

  for (const file of files) {
    if (!alvos.has(file)) continue;

    const source = readFileSync(file, 'utf8');
    if (/<router-outlet/.test(source)) continue;
    if (!LEITURA_DE_DADO.test(source)) continue;
    if (ESCAPE_FALHA.test(source)) continue;
    if (TRATA_FALHA.some(marca => source.includes(marca))) continue;

    problems.push({ file, name: relative(WEB_ROOT, file) });
  }

  return problems;
}

/*
 * `routerLink` apontando para rota que nao existe.
 *
 * O CTA do `gate.component.ts` apontava para `/voce/plano`, que nao esta em `app.routes.ts`:
 * com o curinga `{ path: '**', redirectTo: '/mes' }`, quem decidisse assinar era despejado no
 * Mes sem explicacao. Link morto e ruim em qualquer lugar e pessimo num paywall.
 *
 * Le a arvore de `app.routes.ts` de verdade, com `children`, e nao a lista de literais: e a
 * composicao pai/filho que decide se `/voce/plano` existe.
 */
function arrayBalanceado(texto, abre) {
  let profundidade = 0;
  for (let i = abre; i < texto.length; i++) {
    if (texto[i] === '[') profundidade++;
    else if (texto[i] === ']') {
      profundidade--;
      if (profundidade === 0) return texto.slice(abre + 1, i);
    }
  }
  return '';
}

function objetosDeArray(corpo) {
  const saida = [];
  let profundidade = 0;
  let inicio = -1;
  for (let i = 0; i < corpo.length; i++) {
    if (corpo[i] === '{') {
      if (profundidade === 0) inicio = i;
      profundidade++;
    } else if (corpo[i] === '}') {
      profundidade--;
      if (profundidade === 0) saida.push(corpo.slice(inicio, i + 1));
    }
  }
  return saida;
}

function coletarRotas(corpo, prefixo, into) {
  for (const obj of objetosDeArray(corpo)) {
    const achado = obj.match(/(?:^|[\s{,])path:\s*'([^']*)'/);
    if (!achado) continue;

    const segmento = achado[1];
    const completo = segmento === '' ? prefixo : `${prefixo}/${segmento}`;
    into.add(completo || '/');

    const onde = obj.indexOf('children:');
    if (onde >= 0) {
      const abre = obj.indexOf('[', onde);
      if (abre >= 0) coletarRotas(arrayBalanceado(obj, abre), completo, into);
    }
  }
}

function rotasDeclaradas() {
  const fonte = readFileSync(join(SRC, 'app', 'app.routes.ts'), 'utf8');
  const inicio = fonte.indexOf('[', fonte.indexOf('export const routes'));
  const rotas = new Set();
  coletarRotas(arrayBalanceado(fonte, inicio), '', rotas);
  return rotas;
}

/** Casa o caminho pedido contra os padroes declarados, tratando `:param`. */
function rotaExiste(caminho, declaradas) {
  if (declaradas.has(caminho)) return true;

  const pedidos = caminho.split('/').filter(Boolean);
  for (const padrao of declaradas) {
    if (!padrao.includes(':')) continue;
    const partes = padrao.split('/').filter(Boolean);
    if (partes.length !== pedidos.length) continue;
    if (partes.every((parte, i) => parte.startsWith(':') || parte === pedidos[i])) return true;
  }
  return false;
}

const LINK_LITERAL = /routerLink]?="'?(\/[A-Za-z0-9\-_/]*)'?"/g;

function linkParaRotaInexistente(files) {
  const declaradas = rotasDeclaradas();
  const problems = [];

  for (const file of files) {
    if (file.endsWith('app.routes.ts')) continue;
    const source = readFileSync(file, 'utf8');

    for (const match of source.matchAll(LINK_LITERAL)) {
      const caminho = match[1].replace(/\/$/, '') || '/';
      if (rotaExiste(caminho, declaradas)) continue;

      problems.push({ file, name: `${relative(WEB_ROOT, file)}: ${caminho}` });
    }
  }

  return problems;
}

function aviso(title, problems, hint) {
  if (problems.length === 0) return;
  console.warn(`⚠ ${title} (aviso, não reprova)`);
  const nomes = [...new Set(problems.map(p => p.name))].sort();
  for (const nome of nomes) console.warn(`  ${nome}`);
  console.warn(`  ${hint}`);
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

  /*
   * `.html` filtrava tudo: os componentes deste repo escrevem o template no proprio `.ts`, e o
   * unico `.html` de `src/` e o `index.html`. Estas duas regras rodavam contra ele havia meses --
   * a de explicabilidade e a que o CLAUDE.md chama de invariante, e as telas carregavam
   * `design-exception: explicabilidade` para uma maquina que nao lia.
   */
  const semExplicacao = missingExplainers(templates);
  const semTabela = missingChartAlternatives(templates);
  const semNome = missingAccessibleNames(templates);
  const semFaixa = projectionsWithoutBand(templates);
  const comCerteza = certaintyLanguage(templates);
  const vocabularioGenerico = vocabularioDeIA(tsFiles);
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
  const caixaSolta = caixaMontadaAMao(templates);
  const esqueletoSolto = esqueletoImprovisado(templates);
  const direcaoSolta = direcaoForaDeTabela(templates);
  const becoSemSaida = desabilitadoSemMotivo(templates);
  const contornoInvisivel = contornoDeSeparador(walk(SRC, /\.css$/));
  const falhaSemSaida = telaSemTratarFalha(templates);
  const linkMorto = linkParaRotaInexistente(templates);

  aviso(
    'Raio fora da escala, ou raio de flutuante no que está no chão',
    raioSolto,
    'São quatro: rounded-sm (marca), rounded-md (assentado), rounded-lg (só o que flutua, ' +
      'e flutuar é ter sombra) e rounded-pill. Quatro raios é preferência bem fundamentada, ' +
      'não erro silencioso — por isso avisa e não reprova.'
  );
  aviso(
    'Ícone decorando título',
    tituloDecorado,
    'Ao lado de um título o ícone não acrescenta informação — faz a seção parecer cabeçalho ' +
      'de card de painel. Previne um cheiro real, mas mantém lista de exceção por nome de ' +
      'arquivo, e regra que precisa conhecer nomes de arquivo é revisão com passos extras.'
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
        '<!-- design-exception: explicabilidade — o número já vem explicado no bloco pai -->'
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
      'Vocabulário de IA genérica em texto de tela',
      vocabularioGenerico,
      'A lista está em docs/design/AI-TELLS.md: marketing genérico, fala de assistente, ' +
        'persona de chatbot, emoji e comemoração. Estado é papel de cor, não glifo. ' +
        'Escape: <!-- design-exception: vocabulario — motivo -->'
    ) +
    report(
      'Tipografia fora da escala de papéis',
      tipoCru,
      'Use o papel: fi-body, fi-caption, fi-label, fi-title, fi-eyebrow, fi-metric, ' +
        'fi-metric-sm, fi-money-lg, fi-money-xl, fi-verdict, fi-verdict-sm, fi-ticker. ' +
        'Tamanho solto reabre a decisão a cada tela.'
    ) +
    report(
      'Camada escrita como número',
      camadaSolta,
      'Use o nome da camada: z-nav, z-drawer, z-drawer-panel, z-sheet, z-popover, ' +
        'z-loader, z-toast. Número solto — arbitrário (z-[201]) ou da escala do Tailwind ' +
        '(z-50, que fica abaixo de z-nav) — reabre a ordem de empilhamento a cada tela, e ' +
        'foi assim que o loader foi parar atrás dos modais. Camada local declara o motivo: ' +
        '<!-- design-exception: camada — motivo -->'
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
      'Use .btn-primary, .btn-secondary, .btn-icon, .btn-link, .btn-quiet, .menu-item, ' +
        '.segmented-option ' +
        'ou .input. Se este controle é mesmo único, declare o motivo no arquivo: ' +
        '<!-- design-exception: controle — motivo -->'
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
        '<!-- design-exception: veredito — o veredito de saúde da carteira -->'
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
        'caixa. Se esta caixa é mesmo única: <!-- design-exception: caixa — motivo -->'
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
      'routerLink aponta para rota que não existe',
      linkMorto,
      'O curinga manda o link morto para /mes sem explicação. Ou crie a rota em ' +
        'app.routes.ts, ou corrija o alvo — e num paywall isto é o pior lugar ' +
        'possível para um botão que não leva a nada.'
    ) +
    report(
      'Tela de rota lê dado e não diz quando a leitura falha',
      falhaSemSaida,
      'Envolva o corpo em <app-async-state [loading] [error] [empty] (retry)>. Sem isso a ' +
        'falha de rede sai como tela vazia, e "não conseguimos ler" fica indistinguível de ' +
        '"você não tem nada". Se esta tela realmente não lê nada de fora: ' +
        '<!-- design-exception: falha — motivo -->'
    ) +
    report(
      'Contorno de controle desenhado com o token de separador',
      contornoInvisivel,
      'Use --fi-control-border. hairline é decoração: com ele o contorno de ' +
        '.btn-secondary ficou a 1,20:1 no tema claro, contra os 3:1 que a WCAG ' +
        '1.4.11 pede do limite de um controle.'
    );

  if (problems > 0) {
    console.error(`\n${problems} problema(s) que quebram a tela sem quebrar o build.\n`);
    process.exit(1);
  }

  console.log(
    '✓ Ícones, classes, explicabilidade, gráficos, nomes, faixas, linguagem, ' +
      'tipografia, camada, foco, controles, nome de tela, serifa, ' +
      'ordem de cabeçalho, caixa, esqueleto, direção, ' +
      'estado desabilitado, contorno de controle, tratamento de falha, ' +
      'alvo de link e vocabulario conferidos.'
  );
}

main();
