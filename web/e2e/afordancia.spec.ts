import { expect, test, type Page } from '@playwright/test';
import { entrarComo, salvarPosicao } from './sessao';

/*
 * Um controle tem de se distinguir do que está atrás dele.
 *
 * A WCAG 1.4.11 pede 3:1 do contorno de um controle contra o fundo adjacente. O produto
 * desenhava o contorno de `.btn-secondary` e `.btn-icon` com `hairline`, o mesmo token do
 * separador de linha de tabela: 1,24:1 no tema claro. Foi a queixa "botão que não parece ser
 * botão", e nenhuma revisão visual a pegou porque a borda existia — ela só não era visível.
 *
 * `check-contrast.mjs` cobra os tokens. Este teste cobra o que chega na tela: a cor computada
 * do que o navegador realmente pintou, com os temas alternados pelo atributo que o produto usa.
 */

const CONTROLES = ['.btn-primary', '.btn-secondary', '.btn-icon', '.input'];
const PISO = 3.0;

async function instalarMedidor(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const canal = (v: number) => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    };

    const rgb = (cor: string): [number, number, number, number] => {
      const n = cor.match(/[\d.]+/g)?.map(Number) ?? [0, 0, 0];
      return [n[0] ?? 0, n[1] ?? 0, n[2] ?? 0, n[3] ?? 1];
    };

    const luminancia = (cor: string) => {
      const [r, g, b] = rgb(cor);
      return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b);
    };

    /** O fundo efetivo: o primeiro ancestral que pinta algo opaco. */
    const fundoDe = (el: Element | null): string => {
      let atual: Element | null = el;
      while (atual) {
        const cor = getComputedStyle(atual).backgroundColor;
        if (rgb(cor)[3] > 0.95) return cor;
        atual = atual.parentElement;
      }
      return getComputedStyle(document.body).backgroundColor;
    };

    (window as unknown as Record<string, unknown>)['__fiContraste'] = (seletor: string) => {
      const el = document.querySelector(seletor);
      if (!el) return null;

      const estilo = getComputedStyle(el);
      const atras = fundoDe(el.parentElement);
      const razao = (a: string, b: string) => {
        const [x, y] = [luminancia(a), luminancia(b)].sort((p, q) => q - p);
        return (x + 0.05) / (y + 0.05);
      };

      const proprioFundo = estilo.backgroundColor;
      const temFundo = rgb(proprioFundo)[3] > 0.95;

      return {
        seletor,
        borda: razao(estilo.borderTopColor, atras),
        fundo: temFundo ? razao(proprioFundo, atras) : null,
        rotulo: razao(estilo.color, temFundo ? proprioFundo : atras),
      };
    };
  });
}

for (const tema of ['light', 'dark'] as const) {
  test.describe(`um controle se distingue do fundo — tema ${tema}`, () => {
    test.beforeEach(async ({ page }) => {
      await instalarMedidor(page);
      await entrarComo(page, `e2e_afordancia_${tema}`);
      /*
       * O tema entra pelo mesmo canal do produto. Escrever `data-theme` direto no
       * <html> nao funciona: o script de tema do index.html roda depois e reescreve o
       * atributo a partir do localStorage — o que fazia os dois temas medirem o claro.
       */
      await page.addInitScript(t => {
        localStorage.setItem('fiance.theme', t);
      }, tema);
    });

    test('o contorno de cada controle alcança 3:1 contra o que está atrás', async ({ page }) => {
      await page.goto('/voce');
      await expect(page.locator('header')).toBeVisible();
      await page.waitForLoadState('networkidle');

      let medidos = 0;

      for (const seletor of CONTROLES) {
        const medida = await page.evaluate(
          s => (window as unknown as Record<string, (x: string) => unknown>)['__fiContraste'](s),
          seletor
        );
        if (!medida) continue;
        medidos++;

        const m = medida as { borda: number; fundo: number | null; rotulo: number };

        /*
         * Contorno OU preenchimento serve. Um botão primário se distingue pelo fundo cheio;
         * um secundário, pelo contorno. Exigir os dois proibiria o preenchido, e exigir
         * nenhum é o que produziu o defeito.
         */
        const limite = Math.max(m.borda, m.fundo ?? 0);
        expect(
          limite,
          `${seletor}: nem contorno (${m.borda.toFixed(2)}:1) nem preenchimento ` +
            `(${(m.fundo ?? 0).toFixed(2)}:1) alcançam ${PISO}:1 contra o fundo — ` +
            'é o "botão que não parece ser botão"'
        ).toBeGreaterThanOrEqual(PISO);

        expect(m.rotulo, `${seletor}: o rótulo não é legível sobre o próprio controle`).
          toBeGreaterThanOrEqual(4.5);
      }

      expect(medidos, 'nenhum controle do sistema foi encontrado para medir').toBeGreaterThan(0);
    });
  });
}

test('a barra de progresso distingue preenchido de vazio', async ({ page }) => {
  await instalarMedidor(page);
  await entrarComo(page, 'e2e_progresso');
  await salvarPosicao(page, 'e2e_progresso', 'PETR4', 100, 30);
  await page.goto('/estrategia/metas');
  await expect(page.locator('header')).toBeVisible();
  await page.waitForLoadState('networkidle');

  /*
   * O alvo vem do campo, e sem alvo a régua fica tracejada de propósito — "não sei" não é
   * progresso zero. Declarar a meta pela tela é o que um titular faz, e é o estado em que a
   * barra precisa mostrar quanto do caminho já foi.
   */
  await page.locator('#meta-renda').fill('5000');

  /*
   * Com meta declarada e nenhum provento recebido o progresso e 0%, e o preenchimento tem
   * largura zero — mas ja tem cor. E a cor que este teste mede: a largura e dado, o par de
   * cores e o sistema.
   */
  await expect
    .poll(() =>
      page.evaluate(() => {
        const el = document.querySelector('app-goal-progress .fi-ruler-fill');
        return el ? getComputedStyle(el).backgroundColor : null;
      })
    )
    .not.toBe('rgba(0, 0, 0, 0)');

  const medida = await page.evaluate(() => {
    const poco = document.querySelector('app-goal-progress .fi-ruler');
    const cheio = poco?.querySelector('.fi-ruler-fill');
    if (!poco || !cheio) return null;

    const canal = (v: number) => {
      const c = v / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    };
    const lum = (cor: string) => {
      const n = cor.match(/[\d.]+/g)?.map(Number) ?? [0, 0, 0];
      return 0.2126 * canal(n[0]) + 0.7152 * canal(n[1]) + 0.0722 * canal(n[2]);
    };

    const a = lum(getComputedStyle(cheio).backgroundColor);
    const b = lum(getComputedStyle(poco).backgroundColor);
    const [x, y] = [a, b].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  });

  expect(
    medida,
    'preenchido e vazio precisam se distinguir a 3:1, senão a barra não mostra progresso — ' +
      'era a queixa "barra de progresso que não deixa evidente o progresso"'
  ).toBeGreaterThanOrEqual(PISO);
});

test('utilitaria de layout vence a classe de controle', async ({ page }) => {
  await entrarComo(page, 'e2e_camada');
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto('/hoje');
  await expect(page.locator('header')).toBeVisible();
  await page.waitForLoadState('networkidle');

  /*
   * As classes de controle eram escritas soltas depois de `@tailwind utilities`, e por isso
   * venciam as utilitarias: `class="btn-secondary hidden sm:inline-flex"` ficava VISIVEL,
   * porque `.btn-secondary { display: inline-flex }` derrotava o `display: none` do `hidden`.
   * Valia para todo .btn-* do produto, e nao havia erro nenhum -- esconder um botao por
   * breakpoint simplesmente nao fazia nada. O sintoma que apareceu foi outro: o cabecalho
   * vazando 3px em 320px, nas cinco rotas.
   */
  const escondido = page.locator('header .btn-secondary.hidden').first();
  if ((await escondido.count()) === 0) test.skip();

  const display = await escondido.evaluate(el => getComputedStyle(el).display);
  expect(
    display,
    'um controle do sistema marcado com `hidden` tem de desaparecer: sem isto, nenhuma ' +
      'utilitaria de layout alcanca .btn-*, e o produto esconde botao sem esconder nada'
  ).toBe('none');
});
