import { expect, test } from '@playwright/test';
import { entrarComo, salvarPosicao } from './sessao';

const DESTINOS = ['/hoje', '/carteira', '/descobrir', '/estrategia', '/voce'];

const ANINHADAS = ['/carteira/posicoes', '/descobrir/oportunidades', '/voce/preferencias'];

test.describe('sem sessão', () => {
  test('a entrada é a tela de login', async ({ page }) => {
    await page.goto('/hoje');

    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('link direto renderiza', () => {
  test.beforeEach(async ({ page }) => {
    await entrarComo(page, 'e2e_rotas');
  });

  for (const rota of [...DESTINOS, ...ANINHADAS]) {
    test(`${rota} não abre em branco`, async ({ page }) => {
      const falhas: string[] = [];
      page.on('console', m => {
        if (m.type() === 'error' && m.text().includes('module script')) falhas.push(m.text());
      });

      await page.goto(rota);

      await expect(page.locator('header')).toBeVisible();
      expect(falhas, 'chunk servido como HTML: falta <base href> ou o estático não pega').toEqual(
        []
      );
    });
  }
});

test.describe('a carteira do servidor chega na tela', () => {
  test('a posição salva aparece', async ({ page }) => {
    await entrarComo(page, 'e2e_carteira');
    await salvarPosicao(page, 'e2e_carteira', 'PETR4', 100, 30);

    await page.goto('/carteira/posicoes');

    await expect(page.getByText('PETR4').first()).toBeVisible({ timeout: 30_000 });
  });
});

/**
 * A rota de aquisição, anônima e renderizada no servidor.
 *
 * O E2E existe porque `/voce/preferencias` abria em branco por link direto — e
 * não tocava justamente a única rota com SSR, que é o canal de aquisição
 * inteiro do produto. Aqui ela é exercitada sem sessão, que é como o robô e o
 * visitante de link compartilhado chegam.
 */
test.describe('a página pública de ativo', () => {
  test('abre sem sessão e traz o ticker no HTML do servidor', async ({ page }) => {
    const resposta = await page.goto('/ativo/PETR4');

    expect(resposta?.status()).toBe(200);
    await expect(page).toHaveURL(/\/ativo\/PETR4/);
    await expect(page.getByText('PETR4').first()).toBeVisible({ timeout: 30_000 });
  });

  test('ticker inexistente devolve 404 e se marca como não indexável', async ({ page }) => {
    const resposta = await page.goto('/ativo/NAOEXISTE99');

    // Antes era 200 com o título genérico do index.html — e o sitemap anuncia
    // ~400 tickers, então uma queda da fonte produzia centenas de páginas
    // idênticas, sem noindex para conter.
    expect(resposta?.status()).toBe(404);
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', /noindex/, {
      timeout: 30_000,
    });
  });

  test('o robots fecha tudo e abre só a página de ativo', async ({ request }) => {
    const corpo = await (await request.get('/robots.txt')).text();

    expect(corpo).toContain('Allow: /ativo/');
    expect(corpo).toContain('Disallow: /');
  });
});
