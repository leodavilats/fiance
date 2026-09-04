import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';
import { FiDensity } from '../design-tokens';
import { RecommendService } from './recommend.service';

const DEFAULT_DENSITY: FiDensity = 'comfortable';

@Injectable({ providedIn: 'root' })
export class DensityService {
  private readonly api = inject(RecommendService);
  private readonly doc = inject(DOCUMENT);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  readonly density = signal<FiDensity>(DEFAULT_DENSITY);

  private loaded = false;

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
