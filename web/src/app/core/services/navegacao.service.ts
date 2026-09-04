import { Injectable, inject, signal } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs/operators';

export interface Origem {
  readonly url: string;
  readonly label: string;
}

@Injectable({ providedIn: 'root' })
export class NavegacaoService {
  private readonly router = inject(Router);

  private readonly anterior = signal<string | null>(null);
  private atual: string | null = null;

  constructor() {
    this.router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(e => {
      const url = (e as NavigationEnd).urlAfterRedirects;
      if (this.atual && this.atual !== url) this.anterior.set(this.atual);
      this.atual = url;
    });
  }

  origem(): Origem | null {
    const url = this.anterior();
    if (!url) return null;

    const caminho = url.split('?')[0];
    const label = LABELS.find(([prefixo]) => caminho.startsWith(prefixo))?.[1];
    return label ? { url, label } : null;
  }
}

const LABELS: readonly (readonly [string, string])[] = [
  ['/descobrir/oportunidades', 'às oportunidades'],
  ['/descobrir/quedas', 'às quedas'],
  ['/descobrir/comparar', 'à comparação'],
  ['/carteira/posicoes', 'às posições'],
  ['/carteira', 'à carteira'],
  ['/estrategia/aporte', 'ao aporte'],
  ['/estrategia', 'à estratégia'],
  ['/hoje', 'a Hoje'],
];
