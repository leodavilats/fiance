import { HttpErrorResponse } from '@angular/common/http';
import { TimeoutError } from 'rxjs';
import { describe, expect, it } from 'vitest';
import { detalheUtil, mensagemDeErro } from './error-message';

const resposta = (status: number, detail?: unknown) =>
  new HttpErrorResponse({ status, error: detail === undefined ? null : { detail } });

describe('a frase de falha', () => {
  it('não manda a pessoa conferir o servidor', () => {
    const frase = mensagemDeErro(resposta(0));

    expect(
      frase,
      'status 0 é rede do lado de quem usa, não processo do lado de quem opera'
    ).not.toMatch(/backend|servidor|localhost|porta/i);
    expect(frase).toMatch(/conexão/i);
  });

  it('nunca sai como código de status', () => {
    for (const status of [0, 400, 401, 404, 409, 418, 422, 429, 500, 502, 503]) {
      const frase = mensagemDeErro(resposta(status));

      expect(frase, `status ${status} vazou como número`).not.toMatch(/\b(erro|error)\s*\d/i);
      expect(frase.length, `status ${status} saiu sem frase`).toBeGreaterThan(20);
    }
  });

  it('diz o que não deu, usando a ação de quem chamou', () => {
    expect(mensagemDeErro(resposta(418), 'carregar suas posições')).toContain(
      'carregar suas posições'
    );
  });

  it('separa demora de indisponibilidade', () => {
    expect(mensagemDeErro(new TimeoutError())).toMatch(/demorou/i);
    expect(mensagemDeErro(resposta(503))).toMatch(/instável/i);
  });

  it('sessão vencida é convite a entrar, não falha de dado', () => {
    expect(mensagemDeErro(resposta(401))).toMatch(/sessão/i);
    expect(mensagemDeErro(resposta(403))).toMatch(/sessão/i);
  });
});

describe('o detalhe que o servidor manda', () => {
  it('passa quando é 4xx de domínio, que é escrito para ser lido', () => {
    expect(detalheUtil(resposta(422, 'Quantidade acima da posição'))).toBe(
      'Quantidade acima da posição'
    );
  });

  it('não passa em 5xx nem em queda de rede, que é rastreamento', () => {
    expect(detalheUtil(resposta(500, 'IntegrityError on table portfolio'))).toBeNull();
    expect(detalheUtil(resposta(0, 'connect ECONNREFUSED'))).toBeNull();
  });

  it('ignora detalhe que não é texto', () => {
    expect(detalheUtil(resposta(422, { campo: 'ticker' }))).toBeNull();
    expect(detalheUtil(resposta(422, '   '))).toBeNull();
  });
});
