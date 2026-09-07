import { describe, expect, it } from 'vitest';
import { limparCaminho, limparEvento, limparTexto } from './telemetry';

describe('telemetria não vaza carteira', () => {
  describe('o caminho não entrega o papel', () => {
    it('ticker vira marcador', () => {
      expect(limparCaminho('/ativo/PETR4')).toBe('/ativo/{id}');
      expect(limparCaminho('/ativo/HGLG11/historico')).toBe('/ativo/{id}/historico');
    });

    it('id numérico e identificador longo também', () => {
      expect(limparCaminho('/renda-fixa/4821')).toBe('/renda-fixa/{id}');
      expect(limparCaminho('/api/transactions/0f9c1a2b3d4e5f60')).toBe('/api/transactions/{id}');
    });

    it('a rota continua reconhecível, senão o erro não tem onde ser procurado', () => {
      expect(limparCaminho('/patrimonio/encerradas')).toBe('/patrimonio/encerradas');
    });

    it('mantém o host e descarta query e âncora', () => {
      expect(limparCaminho('https://fiance.app/ativo/VALE3?destaque=1#top')).toBe(
        'https://fiance.app/ativo/{id}'
      );
    });
  });

  describe('o texto não entrega o valor', () => {
    it('redige valor em reais', () => {
      expect(limparTexto('lucro de R$ 38.400,00')).not.toContain('38');
    });

    it('redige número citado em erro de validação', () => {
      const limpo = limparTexto('Quantidade de venda (300) maior que a carteira (100).');

      expect(limpo).not.toContain('300');
      expect(limpo).toContain('Quantidade de venda');
    });

    it('redige segredo em URL', () => {
      expect(limparTexto('GET /api/quote?token=segredo123')).not.toContain('segredo123');
    });
  });

  describe('o evento inteiro', () => {
    const evento = () => ({
      message: 'falhou ao vender R$ 12.500,00',
      request: {
        method: 'POST',
        url: 'https://fiance.app/carteira/PETR4',
        headers: { 'X-Request-Id': 'req-1', Authorization: 'Bearer segredo', Cookie: 'a=b' },
      },
      user: { id: 'u_123', email: 'alguem@exemplo.com' },
      extra: { posicao: { ticker: 'PETR4', avg_price: 38.4 } },
      breadcrumbs: [{ message: 'GET /api/asset/PETR4', data: { avg_price: 38.4 } }],
      exception: { values: [{ value: 'Quantidade de venda (300) maior que a carteira (100).' }] },
    });

    it('só cabeçalho da lista de permissão sai', () => {
      const limpo = limparEvento(evento());

      expect(Object.keys(limpo.request?.['headers'] as object)).toEqual(['X-Request-Id']);
    });

    it('do usuário sai o identificador e mais nada', () => {
      expect(limparEvento(evento()).user).toEqual({ id: 'u_123' });
    });

    it('o dado do breadcrumb não sai', () => {
      expect(limparEvento(evento()).breadcrumbs?.[0].data).toBeUndefined();
    });

    it('nenhum valor da carteira sobrevive no evento serializado', () => {
      const texto = JSON.stringify(limparEvento(evento()));

      for (const vazamento of ['38.4', '12.500', 'alguem@exemplo.com', 'segredo']) {
        expect(texto, `${vazamento} chegaria ao Sentry`).not.toContain(vazamento);
      }
    });
  });
});
