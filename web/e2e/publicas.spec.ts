import { expect, test } from '@playwright/test';

const PUBLICAS = ['/', '/termos', '/privacidade', '/aviso-cvm', '/ativo/PETR4'];

test.describe('quem chega sem sessão fica onde pediu', () => {
  for (const rota of PUBLICAS) {
    test(`${rota} não empurra para o login`, async ({ page }) => {
      await page.goto(rota);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1500);

      expect(
        page.url(),
        `${rota} é pública: um visitante anônimo que caia no login não lê o texto legal, ` +
          'e a loja não valida a URL de privacidade'
      ).not.toContain('/login');
    });
  }

  test('a raiz mostra a landing, e não a casca do app', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    await expect(page.locator('h1')).toContainText('Quanto sobrou este mês');
  });
});
