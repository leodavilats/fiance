#!/usr/bin/env node
/**
 * Os destinos do produto existem nas duas plataformas?
 *
 * Esta é a única verificação automática de paridade, e a justificativa é empírica: o modo de
 * falha que ela cobre já aconteceu e durou meses. O web migrou para o ciclo do dinheiro
 * (`/mes` → `/sobra` → `/patrimonio`) e o mobile ficou em `hoje`/`carteira`/`estrategia`, sem
 * caixa nenhum — metade do produto sem cliente móvel — enquanto `docs/ARCHITECTURE.md`
 * afirmava que o shell do mobile espelhava os destinos do web.
 *
 * O que ela **não** faz: comparar aparência, comparar valor de token, ou gerar arquivo. Ela
 * responde uma pergunta só, a que ninguém fez por tempo suficiente. Espaçamento, composição,
 * navegação e cor continuam livres por plataforma — o contrato é conceito, não implementação.
 *
 * `DIVIDA_HOJE` é catraca, no mesmo padrão de `SEM_MODELO_HOJE` nos testes do backend: não
 * conserta a divergência hoje, não deixa ela crescer, e **reprova quando um item da lista deixa
 * de ser verdade**. Uma lista de dívida que não encolhe é a documentação mentindo de novo.
 *
 * Uso: `node design-tokens/check-parity.mjs`
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const RAIZ = resolve(import.meta.dirname, '..');
const ROTAS_WEB = resolve(RAIZ, 'web', 'src', 'app', 'app.routes.ts');
const ROTAS_MOBILE = resolve(RAIZ, 'mobile', 'lib', 'core', 'router.dart');

/** O ciclo do dinheiro, mais as duas camadas que o cruzam. */
const DESTINOS = ['mes', 'sobra', 'patrimonio', 'descobrir', 'voce'];

/**
 * Divergência conhecida, registrada, e que só pode encolher.
 *
 * **Está vazia, e é assim que ela deve ficar.** O caixa do produto — `cashflow/`,
 * `cashflow_service`, a régua de dívida, a cascata — não tinha tela no mobile quando esta
 * verificação nasceu, e `mes` e `sobra` moraram aqui até as telas existirem (2026-09-08). A
 * catraca cobrou a própria baixa: assim que os destinos passaram a existir, ela reprovou pedindo
 * que as linhas saíssem.
 *
 * Ao registrar uma ausência nova, escreva o nome e o motivo. Ao construí-la, apague a linha —
 * esta verificação reprova se um item daqui passar a existir, porque lista de dívida que não
 * encolhe é a documentação mentindo de novo.
 */
const DIVIDA_HOJE = {
  mobile: [],
  web: [],
};

/** Rota declarada como destino de topo, não como redirect. */
function destinosDoWeb() {
  const fonte = readFileSync(ROTAS_WEB, 'utf8');
  const achados = new Set();
  // `path: 'x'` sem `redirectTo` no mesmo objeto de rota
  for (const bloco of fonte.split(/\{\s*\n?\s*path:/)) {
    const nome = bloco.match(/^\s*'([a-z-]+)'/);
    if (!nome) continue;
    if (/redirectTo/.test(bloco.slice(0, 240))) continue;
    achados.add(nome[1]);
  }
  return achados;
}

function destinosDoMobile() {
  const fonte = readFileSync(ROTAS_MOBILE, 'utf8');
  const achados = new Set();
  for (const [, rota] of fonte.matchAll(/GoRoute\(\s*path:\s*'\/([a-z-]+)'/g)) {
    achados.add(rota);
  }
  // um `redirect:` não é destino: é link antigo honrado
  for (const [, rota] of fonte.matchAll(/path:\s*'\/([a-z-]+)',\s*redirect:/g)) {
    achados.delete(rota);
  }
  return achados;
}

function main() {
  const presentes = { web: destinosDoWeb(), mobile: destinosDoMobile() };
  const falhas = [];

  for (const plataforma of ['web', 'mobile']) {
    const divida = DIVIDA_HOJE[plataforma];

    for (const destino of DESTINOS) {
      const existe = presentes[plataforma].has(destino);
      const registrado = divida.includes(destino);

      if (!existe && !registrado) {
        falhas.push(
          `${plataforma}: o destino "${destino}" não existe, e a ausência não está ` +
            'registrada em DIVIDA_HOJE'
        );
      }
      if (existe && registrado) {
        falhas.push(
          `${plataforma}: "${destino}" está em DIVIDA_HOJE e existe — apague a linha, ` +
            'lista de dívida que não encolhe é a documentação mentindo'
        );
      }
    }

    for (const registrado of divida) {
      if (!DESTINOS.includes(registrado)) {
        falhas.push(
          `${plataforma}: DIVIDA_HOJE lista "${registrado}", que não é um destino do produto`
        );
      }
    }
  }

  if (falhas.length > 0) {
    console.error('');
    console.error('✗ Paridade de conceito entre as plataformas');
    console.error('');
    for (const f of falhas) console.error(`  ${f}`);
    console.error('');
    console.error('  O contrato é conceito, não implementação: o destino existe nas duas');
    console.error('  plataformas, com o mesmo nome e a mesma hierarquia, e cada uma o resolve');
    console.error('  do jeito natural dela. Ausência é dívida registrada, nunca silêncio.');
    console.error('');
    process.exit(1);
  }

  const pendentes = Object.entries(DIVIDA_HOJE)
    .filter(([, v]) => v.length > 0)
    .map(([k, v]) => `${k} ainda sem ${v.join(', ')}`);

  const nota = pendentes.length > 0 ? ` — dívida registrada: ${pendentes.join('; ')}` : '';
  console.log(`✓ Os ${DESTINOS.length} destinos conferidos nas duas plataformas${nota}.`);
}

main();
