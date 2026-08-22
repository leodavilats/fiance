/**
 * Toda cor aqui é `var(--fi-*)`, gerada de `design-tokens/tokens.json` por
 * `design-tokens/build.mjs`. Não escreva hexadecimal neste arquivo.
 *
 * Ver docs/design/06-DESIGN-SYSTEM.md.
 */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        // --- Papéis semânticos (usar estes em código novo) -------------------
        ground: 'var(--fi-ground-0)',
        'ground-1': 'var(--fi-ground-1)',
        'ground-2': 'var(--fi-ground-2)',
        hairline: 'var(--fi-hairline)',
        'hairline-strong': 'var(--fi-hairline-strong)',
        ink: 'var(--fi-ink-1)',
        'ink-2': 'var(--fi-ink-2)',
        'ink-3': 'var(--fi-ink-3)',
        'on-brand': 'var(--fi-ink-on-brand)',
        brand: 'var(--fi-brand)',
        'brand-quiet': 'var(--fi-brand-quiet)',

        // Estado = julgamento do sistema. Sempre mais cromático que direção.
        favorable: 'var(--fi-state-favorable)',
        attention: 'var(--fi-state-attention)',
        adverse: 'var(--fi-state-adverse)',
        indeterminate: 'var(--fi-state-indeterminate)',

        // Direção = aritmética de um número. Croma baixo, de propósito.
        up: 'var(--fi-direction-up)',
        down: 'var(--fi-direction-down)',

        // --- Aliases legados -------------------------------------------------
        // Mantidos porque ~130 usos de bg-accent/text-accent/border-accent vivem
        // em templates que a Fase 8 reescreve. Não use em código novo.
        bg: 'var(--fi-ground-0)',
        'bg-2': 'var(--fi-ground-2)',
        panel: 'var(--fi-ground-1)',
        'panel-2': 'var(--fi-ground-2)',
        tx: 'var(--fi-ink-1)',
        muted: 'var(--fi-ink-2)',
        soft: 'var(--fi-ink-3)',
        accent: 'var(--fi-brand)',
        'accent-2': 'var(--fi-brand)',
        warn: 'var(--fi-state-attention)',
        danger: 'var(--fi-state-adverse)',
        border: 'var(--fi-hairline)',

        // Cores cruas da paleta do Tailwind que os templates atuais usam direto
        // (48 ocorrências, fora de qualquer token). Sobrescritas para dentro do
        // sistema: o significado passa a ser o do papel, não o do número.
        green: { 400: 'var(--fi-state-favorable)' },
        red: { 400: 'var(--fi-state-adverse)' },
        yellow: { 400: 'var(--fi-state-attention)' },
        blue: { 400: 'var(--fi-brand)' },
        purple: { 400: 'var(--fi-series-5)' },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        // A serifa carrega a voz conclusiva: veredito, diagnóstico, resumo.
        serif: ['Source Serif 4', 'ui-serif', 'Georgia', 'serif'],
      },
      boxShadow: {
        theme: 'var(--fi-shadow-popover)',
        drawer: 'var(--fi-shadow-drawer)',
        popover: 'var(--fi-shadow-popover)',
      },
      borderRadius: {
        theme: 'var(--fi-radius-md)',
        sm: 'var(--fi-radius-sm)',
        md: 'var(--fi-radius-md)',
        lg: 'var(--fi-radius-lg)',
      },
      transitionDuration: {
        fast: 'var(--fi-motion-fast)',
        base: 'var(--fi-motion-base)',
        slow: 'var(--fi-motion-slow)',
      },
      screens: {
        // Faixas de docs/design/04-WIREFRAMES.md §10. `md`/`lg`/`xl` já batem
        // com tablet/desktop-sm/desktop nos defaults do Tailwind, então ficam
        // como estão — remapear `sm` (640px, 46 usos hoje) para 420px moveria
        // silenciosamente o layout de todas as telas atuais.
        xs: '420px', // mobile-lg
        '2xl': '1440px', // desktop-lg — 0 usos hoje, então redefinir é de graça
      },
      maxWidth: {
        reading: 'var(--fi-layout-reading-max-width)',
        dense: 'var(--fi-layout-dense-max-width)',
      },
    },
  },
  plugins: [],
};
