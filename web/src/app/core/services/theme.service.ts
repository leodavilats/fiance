import { isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'fiance.theme';

/** O tema do servidor. Escuro porque é o padrão do produto. */
const SERVER_DEFAULT: Theme = 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  /**
   * No servidor não existe `localStorage` nem `matchMedia`, e a preferência é
   * do dispositivo — o HTML renderizado sai no padrão e o navegador corrige na
   * hidratação. Ler storage aqui não daria erro só: daria o tema de outra
   * pessoa se houvesse cache na frente.
   */
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  readonly theme = signal<Theme>(this.detectInitial());

  constructor() {
    if (!this.isBrowser) return;

    this.apply(this.theme());
    if (window.matchMedia && !localStorage.getItem(STORAGE_KEY)) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        const next: Theme = e.matches ? 'dark' : 'light';
        this.theme.set(next);
        this.apply(next);
      });
    }
  }

  toggle(): void {
    const next: Theme = this.theme() === 'dark' ? 'light' : 'dark';
    this.theme.set(next);
    if (this.isBrowser) {
      localStorage.setItem(STORAGE_KEY, next);
      this.apply(next);
    }
  }

  private detectInitial(): Theme {
    if (!this.isBrowser) return SERVER_DEFAULT;

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
