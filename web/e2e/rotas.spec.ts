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
