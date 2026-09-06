import { createHash } from 'node:crypto';
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

test.describe('política de segurança de conteúdo', () => {
  test('o script inline do tema tem hash no CSP, e o hash é o do script servido', async ({
    request,
  }) => {
    const resposta = await request.get('/login');
    const csp = resposta.headers()['content-security-policy'] ?? '';
    const html = await resposta.text();

    const inlines = [...html.matchAll(/<script(?![^>]*\ssrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(
      ([, corpo]) => corpo
    );

    expect(inlines.length, 'o index tem script inline — se deixar de ter, apague este teste').
      toBeGreaterThan(0);

    for (const corpo of inlines) {
      const hash = createHash('sha256').update(corpo).digest('base64');
      expect(
        csp,
        'script inline sem hash no CSP: o navegador o bloqueia e o tema pisca antes de assentar'
      ).toContain(`'sha256-${hash}'`);
    }
  });

  test('o CSP libera o que o login do Google precisa', async ({ request }) => {
    const csp = (await request.get('/login')).headers()['content-security-policy'] ?? '';

    const script = csp.match(/script-src ([^;]*)/)?.[1] ?? '';
    const style = csp.match(/style-src ([^;]*)/)?.[1] ?? '';
    const frame = csp.match(/frame-src ([^;]*)/)?.[1] ?? '';

    expect(script).toContain('https://accounts.google.com');
    expect(style, 'o GIS carrega a própria folha de estilo').toContain(
      'https://accounts.google.com'
    );
    expect(frame).toContain('https://accounts.google.com');
  });
});
