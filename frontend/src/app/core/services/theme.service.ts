import { Injectable, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'fianceai.theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<Theme>(this.detectInitial());

  constructor() {
    this.apply(this.theme());
    if (window.matchMedia && !localStorage.getItem(STORAGE_KEY)) {
      window
        .matchMedia('(prefers-color-scheme: dark)')
        .addEventListener('change', (e) => {
          const next: Theme = e.matches ? 'dark' : 'light';
          this.theme.set(next);
          this.apply(next);
        });
    }
  }

  toggle(): void {
    const next: Theme = this.theme() === 'dark' ? 'light' : 'dark';
    this.theme.set(next);
    localStorage.setItem(STORAGE_KEY, next);
    this.apply(next);
  }

  private detectInitial(): Theme {
    const saved = localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (saved === 'light' || saved === 'dark') return saved;
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  }

  private apply(t: Theme): void {
    document.documentElement.dataset['theme'] = t;
  }
}
