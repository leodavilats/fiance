import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';
import { FiDensity } from '../design-tokens';
import { RecommendService } from './recommend.service';

/** Antes de a preferência chegar do servidor, a tela usa o padrão. */
const DEFAULT_DENSITY: FiDensity = 'comfortable';

/**
 * Densidade de tela, aplicada no documento inteiro.
 *
 * O CSS já sabe reagir a `[data-density]` — os tokens definem altura de linha,
 * espaçamento de seção e padding de bloco por perfil. O que faltava era alguém
 * escrever o atributo, e a partir de uma fonte que faça sentido.
 *
 * **A preferência mora na conta, não no navegador.** Densidade é apetite por
 * informação, e isso acompanha a pessoa, não o aparelho: quem lê tabela densa
 * lê densa no notebook e no celular. É o oposto do tema, que é preferência do
 * dispositivo e por isso vive em `localStorage`.
 */
@Injectable({ providedIn: 'root' })
export class DensityService {
  private readonly api = inject(RecommendService);
  private readonly doc = inject(DOCUMENT);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  readonly density = signal<FiDensity>(DEFAULT_DENSITY);

  private loaded = false;

  /**
   * Busca a preferência uma vez por sessão.
   *
   * Falha silenciosa é a resposta certa aqui: densidade errada é uma tela mais
   * larga do que a pessoa queria, e derrubar a navegação por causa disso seria
   * desproporcional.
   */
  ensureLoaded(): void {
    if (this.loaded || !this.isBrowser) return;
    this.loaded = true;

    this.api.getPreferences().subscribe({
      next: prefs => this.apply((prefs.density as FiDensity) ?? DEFAULT_DENSITY),
      error: () => this.apply(DEFAULT_DENSITY),
    });
  }

  set(density: FiDensity): void {
    this.apply(density);
    this.api.savePreferences({ density }).subscribe({ error: () => undefined });
  }

  private apply(density: FiDensity): void {
    this.density.set(density);
    if (this.isBrowser) {
      this.doc.documentElement.dataset['density'] = density;
    }
  }
}
