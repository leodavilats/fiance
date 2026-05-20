/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        bg:        'var(--bg)',
        'bg-2':    'var(--bg-2)',
        panel:     'var(--panel)',
        'panel-2': 'var(--panel-2)',
        tx:        'var(--text)',
        muted:     'var(--muted)',
        soft:      'var(--soft)',
        accent:    'var(--accent)',
        'accent-2':'var(--accent-2)',
        warn:      'var(--warn)',
        danger:    'var(--danger)',
        border:    'var(--border)',
      },
      boxShadow: {
        theme: 'var(--shadow)',
      },
      borderRadius: {
        theme: 'var(--radius)',
      },
    },
  },
  plugins: [],
};
