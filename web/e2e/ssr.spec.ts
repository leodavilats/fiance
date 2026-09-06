import { expect, test } from '@playwright/test';

const SERVIDAS = [
  { rota: '/ativo/PETR4', contem: 'PETR4' },
  { rota: '/termos', contem: 'Termos de Uso' },
  { rota: '/privacidade', contem: 'Política de Privacidade' },
  { rota: '/aviso-cvm', contem: 'Aviso CVM' },
];

test.describe('renderização no servidor', () => {
  for (const { rota, contem } of SERVIDAS) {
    test(`${rota} chega pronta, sem depender de JavaScript`, async ({ request }) => {
      const resposta = await request.get(rota);

      expect(resposta.status(), `${rota} deveria responder 200`).toBe(200);

      const html = await resposta.text();

      expect(html, `${rota} veio sem conteúdo — o robô receberia página em branco`).toContain(
        contem
      );
      expect(html.length).toBeGreaterThan(25_000);
    });
  }

  test('rota de sessão continua sendo casca, e não vaza conteúdo', async ({ request }) => {
    const html = await (await request.get('/hoje')).text();

    expect(html).not.toContain('Termos de Uso');
    expect(html.length).toBeLessThan(25_000);
  });
});
