import { Injectable, inject, signal } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs/operators';

/** De onde a pessoa veio, e como chamar esse lugar de volta. */
export interface Origem {
  readonly url: string;
  readonly label: string;
}

/**
 * O caminho de onde a pessoa veio, dentro do app.
 *
 * Existe por causa de `/ativo/:ticker`, que é uma **camada** e não um destino:
 * quem chega ali veio de uma lista com filtros na URL, e a página não oferecia
 * volta nenhuma. Um link para `/descobrir/oportunidades` seria pior que o botão
 * do navegador, porque abriria a lista sem os filtros — por isso o retorno usa
 * a URL anterior inteira, com a query preservada.
 *
 * Guarda só a anterior. Uma pilha própria concorreria com o histórico do
 * navegador, que é quem manda.
 */
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

  /**
   * A origem, quando ela é um lugar com nome.
   *
   * Volta `null` quando a pessoa chegou direto — link compartilhado, robô, ou
   * a primeira tela da sessão. Nesse caso não há para onde voltar, e inventar
   * um destino seria pior que não oferecer nenhum.
   */
  origem(): Origem | null {
    const url = this.anterior();
    if (!url) return null;

    const caminho = url.split('?')[0];
    const label = LABELS.find(([prefixo]) => caminho.startsWith(prefixo))?.[1];
    return label ? { url, label } : null;
  }
}

/** Do mais específico para o mais geral: a primeira que casar vence. */
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
