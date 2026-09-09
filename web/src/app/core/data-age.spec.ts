import { describe, expect, it } from 'vitest';
import { carimboMaisAntigo, dadoEnvelhecido, idadeDoDado } from './data-age';

const AGORA = Date.UTC(2026, 8, 9, 12, 0, 0);
const segundos = (minutosAtras: number) => AGORA / 1000 - minutosAtras * 60;

describe('a idade de um dado externo', () => {
  it('cala quando a fonte não carimbou', () => {
    expect(idadeDoDado(null)).toBe('');
    expect(idadeDoDado(undefined)).toBe('');
    expect(idadeDoDado(0)).toBe('');
  });

  it('vira minuto, hora e depois data', () => {
    expect(idadeDoDado(segundos(0), AGORA)).toBe('agora');
    expect(idadeDoDado(segundos(4), AGORA)).toBe('há 4 min');
    expect(idadeDoDado(segundos(90), AGORA)).toBe('há 1 h');
    expect(idadeDoDado(segundos(60 * 30), AGORA)).toMatch(/^em \d{2}\/\d{2}\/\d{4}$/);
  });

  it('marca como velho só o que não é de hoje', () => {
    expect(dadoEnvelhecido(segundos(59), AGORA)).toBe(false);
    expect(dadoEnvelhecido(segundos(60 * 23), AGORA)).toBe(false);
    expect(dadoEnvelhecido(segundos(60 * 25), AGORA)).toBe(true);
    expect(dadoEnvelhecido(null, AGORA), 'sem carimbo não é velho, é sem carimbo').toBe(false);
  });
});

describe('a idade de um conjunto', () => {
  it('é a do mais antigo, senão a tabela promete frescor que a linha de baixo não tem', () => {
    expect(carimboMaisAntigo([segundos(2), segundos(40), segundos(9)])).toBe(segundos(40));
  });

  it('ignora ausência sem virar zero', () => {
    expect(carimboMaisAntigo([null, segundos(5), undefined, 0])).toBe(segundos(5));
    expect(carimboMaisAntigo([null, undefined])).toBeNull();
    expect(carimboMaisAntigo([])).toBeNull();
  });
});
