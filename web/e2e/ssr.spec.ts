import { createHash } from 'node:crypto';
import { expect, test } from '@playwright/test';

function dentroDoAppRoot(html: string): string {
  return html.match(/<app-root[^>]*>([\s\S]*?)<\/app-root>/)?.[1] ?? '';
}

const SERVIDAS = [
  { rota: '/', contem: 'Quanto sobrou este m' },
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
      expect(
        dentroDoAppRoot(html).length,
        `${rota} tem <app-root> vazio: o HTML chegou, o conteúdo não`
      ).toBeGreaterThan(1_000);
    });
  }

  test('rota de sessão continua sendo casca, e não vaza conteúdo', async ({ request }) => {
    const html = await (await request.get('/mes')).text();

    expect(html).not.toContain('Termos de Uso');
    expect(dentroDoAppRoot(html), 'rota de sessão não pode renderizar no servidor').toBe('');
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

  test('nada de handler inline: hash não vale para eles, e o CSP os bloqueia', async ({
    request,
  }) => {
    const html = await (await request.get('/login')).text();

    const handlers = html.match(/\son[a-z]+\s*=/gi) ?? [];

    expect(
      handlers,
      'o Angular volta a injetar onload="this.media=..." se inlineCritical for religado, ' +
        'e aí a folha de estilo completa nunca é aplicada'
    ).toEqual([]);
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

test.describe('o deploy chega em quem já visitou', () => {
  test('os bundles de entrada têm hash no nome', async ({ request }) => {
    const html = await (await request.get('/')).text();
    const fontes = [...html.matchAll(/(?:src|href)="([^"]*\/?(?:main|polyfills|styles)[^"]*)"/g)].map(
      m => m[1]
    );

    expect(fontes.length, 'a página tem de carregar main, polyfills e styles').toBeGreaterThan(0);

    for (const fonte of fontes) {
      expect(
        fonte,
        `${fonte} sem hash de conteúdo: servido com cache de um ano, ele congela o deploy para ` +
          'quem já visitou o site — a mudança só aparece quando o cache expira'
      ).toMatch(/-[A-Za-z0-9_]{8,}\.(js|css)$/);
    }
  });

  test('o HTML é sempre revalidado, senão ele aponta para o bundle velho', async ({ request }) => {
    const resposta = await request.get('/');
    const cache = resposta.headers()['cache-control'] ?? '';

    expect(cache, 'HTML com cache longo desfaz o hash: o índice fica preso no bundle antigo').toMatch(
      /no-cache|no-store|max-age=0/
    );
  });
});
