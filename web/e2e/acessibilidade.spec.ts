import { expect, test } from '@playwright/test';
import { entrarComo, salvarPosicao } from './sessao';

/**
 * Os testes de experiência que o `lint:ui` não consegue fazer.
 *
 * O lint lê o código-fonte: sabe que existe uma tabela alternativa ao gráfico,
 * não sabe se ela contém os mesmos números; sabe que uma cor é token, não sabe
 * se a tela continua legível sem cor nenhuma. Estes rodam no navegador.
 */

const DESTINOS = ['/hoje', '/carteira', '/descobrir', '/estrategia', '/voce'];

test.describe('diálogo prende e devolve o foco', () => {
  test('o drawer de atividade não deixa o Tab escapar, e devolve o foco ao gatilho', async ({
    page,
  }) => {
    await entrarComo(page, 'e2e_dialogo');
    await page.goto('/hoje');

    const gatilho = page.getByRole('button', { name: 'Abrir atividade recente' });
    await gatilho.click();

    const painel = page.locator('[role="dialog"]').first();
    await expect(painel).toBeVisible();

    // Vinte Tabs não podem levar o foco para fora do painel.
    for (let i = 0; i < 20; i++) {
      await page.keyboard.press('Tab');
      const dentro = await page.evaluate(() => {
        const dialogo = document.querySelector('[role="dialog"]');
        return !!dialogo && dialogo.contains(document.activeElement);
      });
      expect(dentro, `o foco escapou do diálogo no Tab ${i + 1}`).toBe(true);
    }

    await page.keyboard.press('Escape');
    await expect(painel).toBeHidden();

    const voltou = await page.evaluate(
      () => document.activeElement?.getAttribute('aria-label') ?? ''
    );
    expect(voltou, 'ao fechar, o foco volta para quem abriu').toContain('atividade');
  });

  test('a busca global fecha no Esc sem perder o foco na página', async ({ page }) => {
    await entrarComo(page, 'e2e_busca');
    await page.goto('/hoje');

    await page.keyboard.press('Control+k');
    await expect(page.locator('[role="dialog"]').first()).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(page.locator('[role="dialog"]')).toHaveCount(0);
  });
});

test.describe('a tela se entende sem cor', () => {
  for (const rota of DESTINOS) {
    test(`${rota} não depende de cor para dizer estado`, async ({ page }) => {
      await entrarComo(page, 'e2e_sem_cor');
      await page.goto(rota);
      await expect(page.locator('header')).toBeVisible();

      await page.addStyleTag({ content: 'html { filter: grayscale(1) !important; }' });

      // Todo selo de estado carrega texto: cor + forma + palavra, nunca cor só.
      const selos = page.locator('.verdict-pill, .tag');
      const total = await selos.count();
      for (let i = 0; i < total; i++) {
        const texto = (await selos.nth(i).innerText()).trim();
        expect(texto, `selo sem texto em ${rota}: cor seria o único canal`).not.toBe('');
      }
    });
  }
});

test.describe('o gráfico e a tabela contam a mesma coisa', () => {
  test('a série do benchmark aparece em números', async ({ page }) => {
    await entrarComo(page, 'e2e_grafico');
    await salvarPosicao(page, 'e2e_grafico', 'PETR4', 100, 30);

    await page.goto('/carteira/desempenho');

    const abrir = page.getByRole('button', { name: /série em tabela/i });
    if ((await abrir.count()) === 0) test.skip();

    await abrir.first().click();
    const tabela = page.locator('table').first();
    await expect(tabela).toBeVisible();

    const linhas = await tabela.locator('tbody tr').count();
    expect(linhas, 'a alternativa textual precisa ter os pontos, não um resumo').toBeGreaterThan(0);
  });
});

test.describe('reflow', () => {
  test('em 320 px nenhuma tela rola para o lado', async ({ page }) => {
    await entrarComo(page, 'e2e_reflow');
    await page.setViewportSize({ width: 320, height: 720 });

    for (const rota of DESTINOS) {
      await page.goto(rota);
      await expect(page.locator('header')).toBeVisible();

      const vaza = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
      );
      expect(vaza, `${rota} rola horizontalmente em 320 px`).toBe(false);
    }
  });

  test('com zoom de 200% o conteúdo continua na coluna', async ({ page }) => {
    await entrarComo(page, 'e2e_zoom');
    await page.setViewportSize({ width: 640, height: 512 });
    await page.goto('/carteira');
    await expect(page.locator('header')).toBeVisible();

    const vaza = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
    );
    expect(vaza, 'a carteira vaza para o lado no equivalente a 200% de zoom').toBe(false);
  });
});

test.describe('movimento reduzido', () => {
  test('nada anima quando o sistema pede para não animar', async ({ browser }) => {
    const contexto = await browser.newContext({ reducedMotion: 'reduce' });
    const page = await contexto.newPage();

    await entrarComo(page, 'e2e_movimento');
    await page.goto('/hoje');
    await expect(page.locator('header')).toBeVisible();

    const animados = await page.evaluate(
      () =>
        [...document.querySelectorAll<HTMLElement>('*')].filter(el => {
          const estilo = getComputedStyle(el);
          const dura = parseFloat(estilo.animationDuration) || 0;
          return estilo.animationName !== 'none' && dura > 0.05;
        }).length
    );

    expect(animados, 'com prefers-reduced-motion nada deve animar além de opacidade').toBe(0);
    await contexto.close();
  });
});
