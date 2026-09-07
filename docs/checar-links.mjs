#!/usr/bin/env node
/**
 * Link quebrado na documentação.
 *
 * Reorganizar documentação sem conferir link é refatorar sem teste: a árvore fica bonita e
 * metade das referências aponta para o nada. Este script varre todo `.md` do repositório e
 * confere que cada link relativo existe em disco — incluindo âncoras de heading, que são o que
 * quebra em silêncio quando um título muda.
 *
 * Uso: `node docs/checar-links.mjs`
 */

import { readFileSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readdirSync } from 'node:fs';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, '..');

const IGNORAR = new Set(['node_modules', '.git', 'dist', '.angular', 'build', '__pycache__']);

function varrer(dir) {
  const achados = [];
  for (const nome of readdirSync(dir)) {
    if (IGNORAR.has(nome)) continue;
    const caminho = join(dir, nome);
    const info = statSync(caminho);
    if (info.isDirectory()) achados.push(...varrer(caminho));
    else if (nome.endsWith('.md')) achados.push(caminho);
  }
  return achados;
}

/**
 * Como o GitHub gera a âncora de um título: minúsculo, sem pontuação, espaço vira hífen.
 *
 * Duas sutilezas que custaram um falso positivo cada. O espaço vira hífen **um a um**, sem
 * colapsar: um travessão removido deixa dois espaços, e o GitHub gera dois hífens. E os dois
 * lados passam por NFC, porque acento composto e acento pré-composto são strings diferentes
 * para o `===` e a mesma letra para quem lê.
 */
function ancora(titulo) {
  return titulo
    .normalize('NFC')
    .trim()
    .toLowerCase()
    .replace(/[`*[\]()]/g, '')
    .replace(/[^\p{L}\p{N} _-]/gu, '')
    .replace(/ /g, '-');
}

function ancorasDe(caminho) {
  const encontradas = new Set();

  /*
   * O split e por `\r?\n`, e nao por `\n`.
   *
   * Em JavaScript `\r` e terminador de linha, e por isso `.` nao o casa: com CRLF,
   * `/^#+\s+(.*)$/` nao casa cabecalho nenhum. A primeira versao deste script achava ZERO
   * ancoras e reportava trinta links quebrados que estavam certos.
   */
  for (const linha of readFileSync(caminho, 'utf8').split(/\r?\n/)) {
    const m = linha.match(/^#{1,6}\s+(.*)$/);
    if (m) encontradas.add(ancora(m[1]));
  }
  return encontradas;
}

const arquivos = varrer(RAIZ);
const cacheDeAncoras = new Map();
const quebrados = [];

for (const arquivo of arquivos) {
  const texto = readFileSync(arquivo, 'utf8');

  for (const [, , destino] of texto.matchAll(/\[([^\]]*)\]\(([^)\s]+)\)/g)) {
    if (/^(https?:|mailto:|#)/.test(destino)) continue;

    const [caminho, fragmento] = destino.split('#');
    const alvo = resolve(dirname(arquivo), caminho || '.');

    let existe = true;
    try {
      statSync(alvo);
    } catch {
      existe = false;
    }

    if (!existe) {
      quebrados.push(`${relative(RAIZ, arquivo)} → ${destino}`);
      continue;
    }

    if (fragmento && alvo.endsWith('.md')) {
      if (!cacheDeAncoras.has(alvo)) cacheDeAncoras.set(alvo, ancorasDe(alvo));
      if (!cacheDeAncoras.get(alvo).has(fragmento.normalize('NFC'))) {
        quebrados.push(`${relative(RAIZ, arquivo)} → ${destino}  (âncora não existe)`);
      }
    }
  }
}

if (quebrados.length > 0) {
  console.error(`\n✗ ${quebrados.length} link(s) quebrado(s) na documentação\n`);
  for (const q of quebrados) console.error(`  ${q}`);
  console.error('');
  process.exit(1);
}

console.log(`✓ ${arquivos.length} arquivos .md, nenhum link quebrado.`);
