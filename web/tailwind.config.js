/**
 * Toda cor aqui é `var(--fi-*)`, gerada de `design-tokens/tokens.json` por
 * `design-tokens/build.mjs`. Não escreva hexadecimal neste arquivo.
 *
 * Ver docs/design/06-DESIGN-SYSTEM.md.
 */

/**
 * Um token de cor que aceita modificador de opacidade.
 *
 * Uma cor declarada como a string `'var(--fi-x)'` faz o Tailwind **descartar em
 * silêncio** todo modificador (`bg-brand/20` não emitia regra nenhuma, porque o
 * v3 só sabe injetar alfa em `rgb(... / <alpha-value>)`). Como os tokens são
 * hexadecimais, a saída aqui é `color-mix` sobre o próprio token — o alfa passa
 * a existir sem duplicar a cor em formato RGB.
 */
const token = name => {
  const base = `var(--fi-${name})`;
  return ({ opacityValue } = {}) => {
    if (opacityValue === undefined) return base;
    const pct = Number(opacityValue);
    if (!Number.isFinite(pct)) return base;
    return `color-mix(in srgb, ${base} ${pct * 100}%, transparent)`;
  };
};

const series = Object.fromEntries([
  ...Array.from({ length: 11 }, (_, i) => [String(i + 1), token(`series-${i + 1}`)]),
  ['other', token('series-other')],
]);

module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        ground: token('ground-0'),
        'ground-1': token('ground-1'),
        'ground-2': token('ground-2'),
        hairline: token('hairline'),
        'hairline-strong': token('hairline-strong'),
        ink: token('ink-1'),
        'ink-2': token('ink-2'),
        'ink-3': token('ink-3'),
        'on-brand': token('ink-on-brand'),
        brand: token('brand'),
        'brand-quiet': token('brand-quiet'),

        favorable: token('state-favorable'),
        attention: token('state-attention'),
        adverse: token('state-adverse'),
        indeterminate: token('state-indeterminate'),

        /*
         * O chão de um aviso, não a tinta dele.
         *
         * A quantidade de pigmento em cada uma foi escolhida por contraste, não
         * a olho: é a maior que ainda deixa legíveis as duas coisas que ficam
         * em cima — o rótulo, na cor do estado, e o corpo, em tinta primária.
         * `check-contrast.mjs` verifica exatamente esses dois pares.
         */
        'favorable-surface': token('state-favorable-surface'),
        'attention-surface': token('state-attention-surface'),
        'adverse-surface': token('state-adverse-surface'),
        'indeterminate-surface': token('state-indeterminate-surface'),

        up: token('direction-up'),
        down: token('direction-down'),

        series,
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Source Serif 4', 'ui-serif', 'Georgia', 'serif'],
      },
      boxShadow: {
        drawer: 'var(--fi-shadow-drawer)',
        popover: 'var(--fi-shadow-popover)',
      },
      // A escala de camadas, pelo nome. Onze templates escreviam o número
      // mágico direto (`z-[100]`…`z-[400]`, mais um `z-[201]` que nem existia
      // na escala) contra dois consumidores dos tokens — a mesma armadilha de
      // "vocabulário gerado sem consumidor", viva e não detectada. Já tinha
      // produzido um defeito: o loader ficava em 100 e desenhava atrás de
      // modais e drawers, que ficam em 200–300.
      zIndex: {
        nav: 'var(--fi-z-nav)',
        drawer: 'var(--fi-z-drawer)',
        'drawer-panel': 'var(--fi-z-drawer-panel)',
        sheet: 'var(--fi-z-sheet)',
        popover: 'var(--fi-z-popover)',
        loader: 'var(--fi-z-loader)',
        toast: 'var(--fi-z-toast)',
      },
      borderRadius: {
        sm: 'var(--fi-radius-sm)',
        md: 'var(--fi-radius-md)',
        lg: 'var(--fi-radius-lg)',
        pill: 'var(--fi-radius-pill)',
      },
      transitionDuration: {
        fast: 'var(--fi-motion-fast)',
        base: 'var(--fi-motion-base)',
        slow: 'var(--fi-motion-slow)',
      },
      transitionTimingFunction: {
        enter: 'var(--fi-motion-ease-enter)',
        exit: 'var(--fi-motion-ease-exit)',
      },
      screens: {
        xs: '420px',
        '2xl': '1440px',
      },
      maxWidth: {
        reading: 'var(--fi-layout-reading-max-width)',
        dense: 'var(--fi-layout-dense-max-width)',
      },
    },
  },
  plugins: [],
};
