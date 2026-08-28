import { CommonModule } from '@angular/common';
import {
  Component,
  computed,
  ElementRef,
  HostListener,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { GlobalSearchService, SearchDestination } from '../../core';

interface Row {
  readonly kind: 'destination' | 'mine' | 'ticker';
  /** Cabeçalho da seção. Vem do servidor no caso do que é da pessoa. */
  readonly group: string;
  readonly label: string;
  readonly detail: string;
  readonly icon: string;
  readonly route: string;
}

/**
 * Busca global — `⌘K` no Mac, `Ctrl+K` no resto.
 *
 * É ferramenta de navegação, não tela de pesquisa: abre por cima, responde e
 * some.
 *
 * O que é da pessoa vem primeiro — quem digita "PETR" e tem PETR4 na carteira
 * quer a própria posição, não a página do ativo. Depois as telas, que filtram
 * sem rede e por isso continuam funcionando quando a chamada falha. Por último
 * o mercado. Teclado é o caminho principal —
 * setas movem, Enter vai, Esc fecha —, e por isso a lista é uma única sequência
 * navegável, mesmo dividida em seções na tela.
 */
@Component({
  selector: 'app-global-search',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    @if (search.open()) {
      <div
        class="fixed inset-0 z-[300] fi-overlay flex items-start justify-center pt-[12vh] px-4"
        (click)="search.hide()"
      >
        <div
          class="w-full max-w-[560px] bg-ground-1 border border-hairline rounded-lg shadow-popover overflow-hidden"
          (click)="$event.stopPropagation()"
          role="dialog"
          aria-modal="true"
          aria-label="Busca global"
        >
          <div class="flex items-center gap-3 px-4 border-b border-hairline">
            <lucide-icon
              name="search"
              size="16"
              class="text-ink-3"
              aria-hidden="true"
            ></lucide-icon>
            <input
              #field
              type="text"
              class="flex-1 bg-transparent border-0 outline-none text-ink py-4 fi-body"
              style="height: auto; padding: 16px 0; background: transparent !important; border: 0 !important;"
              placeholder="Buscar tela ou ativo…"
              aria-label="Buscar tela ou ativo"
              [value]="search.query()"
              (input)="onInput($event)"
              (keydown)="onKeydown($event)"
            />
            <kbd class="fi-caption text-ink-3 border border-hairline rounded-sm px-1.5 py-0.5"
              >esc</kbd
            >
          </div>

          <div class="max-h-[52vh] overflow-y-auto py-2" role="listbox">
            @if (rows().length === 0) {
              <p class="fi-body text-ink-2 px-4 py-6 m-0">
                Nada encontrado para “{{ search.query() }}”. A busca cobre as telas do app e os
                ativos do universo da B3.
              </p>
            }

            @for (group of groups(); track group.title) {
              <p class="fi-eyebrow text-ink-3 px-4 pt-3 pb-1 m-0">{{ group.title }}</p>
              @for (row of group.rows; track row.route) {
                <button
                  type="button"
                  class="w-full flex items-center gap-3 px-4 py-2.5 text-left bg-transparent border-0 cursor-pointer transition-colors"
                  [class.bg-ground-2]="row === active()"
                  [attr.aria-selected]="row === active()"
                  role="option"
                  (click)="go(row)"
                  (mouseenter)="focusRow(row)"
                >
                  <lucide-icon
                    [name]="row.icon"
                    size="14"
                    class="text-ink-3 shrink-0"
                    aria-hidden="true"
                  ></lucide-icon>
                  <span class="fi-label text-ink truncate">{{ row.label }}</span>
                  <span class="fi-caption text-ink-3 truncate ml-auto">{{ row.detail }}</span>
                </button>
              }
            }

            @if (search.searching()) {
              <p class="fi-caption text-ink-3 px-4 py-2 m-0">Buscando ativos…</p>
            }
          </div>
        </div>
      </div>
    }
  `,
})
export class GlobalSearchComponent {
  readonly search = inject(GlobalSearchService);
  private readonly router = inject(Router);
  private readonly field = viewChild<ElementRef<HTMLInputElement>>('field');

  private readonly cursor = signal(0);

  constructor() {
    effect(() => {
      if (this.search.open()) {
        queueMicrotask(() => this.field()?.nativeElement.focus());
      }
    });
  }

  /** A rota de um achado do servidor. O `ref` é o identificador; o caminho é nosso. */
  private routeFor(kind: string, ref: string): string {
    return kind === 'fixed_income' ? '/carteira/posicoes' : `/ativo/${ref}`;
  }

  readonly rows = computed<Row[]>(() => {
    const mine: Row[] = this.search.mine().flatMap(group =>
      group.items.map(item => ({
        kind: 'mine' as const,
        group: group.label,
        label: item.title,
        detail: item.subtitle,
        icon: item.kind === 'fixed_income' ? 'landmark' : 'wallet',
        route: this.routeFor(item.kind, item.ref),
      }))
    );

    const destinations: Row[] = this.search.destinations().map((d: SearchDestination) => ({
      kind: 'destination' as const,
      group: 'Telas',
      label: d.label,
      detail: d.section,
      icon: d.icon,
      route: d.route,
    }));

    const tickers: Row[] = this.search.tickers().map(t => ({
      kind: 'ticker' as const,
      group: 'Ativos',
      label: t.ticker,
      detail: t.name,
      icon: 'chart-candlestick',
      route: `/ativo/${t.ticker}`,
    }));

    return [...mine, ...destinations, ...tickers];
  });

  readonly groups = computed(() => {
    const ordem = new Map<string, Row[]>();
    for (const row of this.rows()) {
      ordem.set(row.group, [...(ordem.get(row.group) ?? []), row]);
    }
    return [...ordem].map(([title, rows]) => ({ title, rows }));
  });

  readonly active = computed(() => this.rows()[Math.min(this.cursor(), this.rows().length - 1)]);

  /** O atalho vive na janela: a busca precisa abrir de qualquer tela. */
  @HostListener('window:keydown', ['$event'])
  onGlobalKeydown(event: KeyboardEvent): void {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      this.search.toggle();
      this.cursor.set(0);
    }
  }

  onInput(event: Event): void {
    this.search.setQuery((event.target as HTMLInputElement).value);
    this.cursor.set(0);
  }

  onKeydown(event: KeyboardEvent): void {
    const total = this.rows().length;
    if (event.key === 'Escape') {
      event.preventDefault();
      this.search.hide();
    } else if (event.key === 'ArrowDown' && total > 0) {
      event.preventDefault();
      this.cursor.set((this.cursor() + 1) % total);
    } else if (event.key === 'ArrowUp' && total > 0) {
      event.preventDefault();
      this.cursor.set((this.cursor() - 1 + total) % total);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const row = this.active();
      if (row) this.go(row);
    }
  }

  focusRow(row: Row): void {
    this.cursor.set(this.rows().indexOf(row));
  }

  go(row: Row): void {
    this.search.hide();
    this.router.navigateByUrl(row.route);
  }
}
