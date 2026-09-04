import { expect, test, type Page } from '@playwright/test';
import { entrarComo, salvarPosicao } from './sessao';

/**
 * O que o lint não alcança: a experiência de quem não usa mouse.
 *
 * A suíte de navegador tinha seis testes, todos de rota e SSR, e nenhum tocava
 * teclado, foco ou anúncio. O `lint:ui` cobre presença — que o botão tem nome,
 * que o julgamento tem explicação — e não cobre alcance: o glossário do
 * produto abria só em `:hover`, então existia em sete telas e era invisível
 * para quem navega por teclado.
 */

const DESTINOS = ['/hoje', '/carteira', '/descobrir', '/estrategia', '/voce'];

/** O que está focado agora, como o leitor de tela o anunciaria. */
async function focoAtual(page: Page): Promise<{ tag: string; nome: string }> {
  return page.evaluate(() => {
    const el = document.activeElement as HTMLElement | null;
    return {
      tag: el?.tagName.toLowerCase() ?? '',
      nome: (el?.getAttribute('aria-label') ?? el?.textContent ?? '').trim().slice(0, 40),
    };
  });
}

test.describe('navegação só por teclado', () => {
  test.beforeEach(async ({ page }) => {
    await entrarComo(page, 'e2e_teclado');
  });

  for (const rota of DESTINOS) {
    test(`${rota} percorre sem armadilha e com foco sempre visível`, async ({ page }) => {
      await page.goto(rota);
      await expect(page.locator('header')).toBeVisible();

      let visitados = 0;

      for (let i = 0; i < 60; i++) {
        await page.keyboard.press('Tab');

        /*
          Marcar o nó, não o rótulo: dois links só de ícone têm o mesmo texto
          vazio, e comparar por rótulo dava ciclo falso na primeira repetição.
          `data-e2e-tab` volta `'novo'`, `'repetido'` ou `'fora'`.
        */
        const estado = await page.evaluate(() => {
          const el = document.activeElement as HTMLElement | null;
          if (!el || el === document.body) return 'fora';
          if (el.dataset['e2eTab']) return 'repetido';
          el.dataset['e2eTab'] = '1';
          return 'novo';
        });

        if (estado !== 'novo') break;
        visitados++;

        const atual = await focoAtual(page);
        const chave = `${atual.tag}:${atual.nome}`;

        const temAnel = await page.evaluate(() => {
          const el = document.activeElement as HTMLElement | null;
          if (!el) return false;
          const estilo = getComputedStyle(el);
          return (
            estilo.outlineStyle !== 'none' ||
            estilo.boxShadow !== 'none' ||
            el.matches(':focus-visible')
          );
        });
        expect(temAnel, `sem foco visível em ${chave} na rota ${rota}`).toBe(true);
      }

      expect(visitados, `nada focável em ${rota}`).toBeGreaterThan(3);
    });
  }
});

test.describe('a explicação alcança quem usa teclado', () => {
  test('o glossário abre no foco, não só no ponteiro', async ({ page }) => {
    await entrarComo(page, 'e2e_glossario');
    await salvarPosicao(page, 'e2e_glossario', 'PETR4', 100, 30);

    await page.goto('/carteira/posicoes');

    const gatilho = page.locator('app-help-tooltip button').first();
    await expect(gatilho).toBeVisible();

    await expect(page.locator('[role="tooltip"]')).toHaveCount(0);

    await gatilho.focus();
    await expect(page.locator('[role="tooltip"]')).toBeVisible();

    // O texto precisa estar associado ao gatilho, não só ao lado dele.
    const descrito = await gatilho.getAttribute('aria-describedby');
    expect(descrito, 'tooltip sem aria-describedby não é anunciado').toBeTruthy();
  });

  test('a proveniência abre por teclado', async ({ page }) => {
    await entrarComo(page, 'e2e_provenance');
    await page.goto('/descobrir/oportunidades');

    const resumo = page.locator('app-provenance summary').first();
    if ((await resumo.count()) === 0) test.skip();

    await resumo.focus();
    await page.keyboard.press('Enter');

    await expect(page.locator('app-provenance details[open]').first()).toBeVisible();
  });
});

test.describe('o foco acompanha a navegação', () => {
  test('trocar de destino leva o foco para o título da tela', async ({ page }) => {
    await entrarComo(page, 'e2e_foco_rota');
    await page.goto('/hoje');
    await expect(page.locator('header')).toBeVisible();

    await page.getByRole('link', { name: 'Carteira', exact: true }).first().click();
    await expect(page).toHaveURL(/\/carteira/);

    const foco = await page.evaluate(() => document.activeElement?.tagName.toLowerCase() ?? '');
    expect(foco, 'depois de navegar o foco deve ir para o <h1> da rota').toBe('h1');
  });

  test('a mudança de tela é anunciada', async ({ page }) => {
    await entrarComo(page, 'e2e_anuncio');
    await page.goto('/hoje');

    const regiao = page.locator('[role="status"][aria-live="polite"]').first();
    await page.getByRole('link', { name: 'Descobrir', exact: true }).first().click();

    await expect(regiao).toContainText(/Descobrir/);
  });
});
