import { Injectable, signal } from '@angular/core';

/**
 * O estado da camada de atividade.
 *
 * Mora num serviço, e não num `signal` de tela, porque quem abre o drawer (o
 * cabeçalho, `/hoje`) não é quem o desenha (o shell) — um layout com
 * `router-outlet` não recebe `output` de filho roteado.
 */
@Injectable({ providedIn: 'root' })
export class ActivityService {
  readonly open = signal(false);

  show(): void {
    this.open.set(true);
  }

  hide(): void {
    this.open.set(false);
  }

  toggle(): void {
    this.open.update(v => !v);
  }
}
