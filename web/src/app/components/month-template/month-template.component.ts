import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CashMonthTemplate,
  CashTemplateCandidate,
  CashflowService,
  mesCorrente,
  nomeDoMes,
  fiCategoriasDeDespesa,
  fiCategoriasDeEntrada,
} from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-month-template',
  standalone: true,
  imports: [CommonModule, RouterLink, LucideAngularModule, PageHeaderComponent, SkeletonComponent],
  template: `
    <app-page-header
      title="Repetir o mês"
      [question]="pergunta()"
      scope="Nada é gravado enquanto você não confirmar."
    />

    @if (carregando()) {
      <app-skeleton shape="metric" />
    } @else if (erro()) {
      <div class="notice notice-adverse">
        <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
        <div>
          <p class="fi-label m-0">Não foi possível montar o molde</p>
          <p class="fi-body m-0 mt-1">{{ erro() }}</p>
          <a routerLink="/mes" class="btn-secondary compact-btn no-underline mt-3">Voltar ao mês</a>
        </div>
      </div>
    } @else if (candidatos().length === 0) {
      <div class="notice notice-brand">
        <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
        <div>
          <p class="fi-label m-0">{{ nome(origem()) }} não tem nada lançado</p>
          <p class="fi-body m-0 mt-1">
            O molde copia de um mês para o outro, então precisa de um mês de origem. Lance
            {{ nome(destino()) }} à mão desta vez — no mês seguinte ele já serve de molde.
          </p>
          <a routerLink="/mes/lancar" class="btn-primary no-underline mt-3">
            <lucide-icon name="plus" size="16" aria-hidden="true"></lucide-icon>
            Lançar
          </a>
        </div>
      </div>
    } @else {
      <section class="fi-block">
        <p class="fi-body text-ink-2 m-0 max-w-reading">
          Vem marcado o que repete todo mês por natureza — o fixo, a dívida e o salário. Gasto
          variável fica desmarcado: o valor do mês que passou é fato daquele mês, e copiá-lo
          inventaria uma despesa que ainda não existe.
        </p>
        <p class="fi-body text-ink-2 m-0 mt-2 max-w-reading">
          O que for copiado nasce <strong>a vencer</strong>, com o mesmo dia e o valor do mês
          anterior. Onde o valor mudou, é só editar o lançamento depois.
        </p>

        <div class="overflow-x-auto mt-4">
          <table class="data-table">
            <caption class="sr-only">
              Lançamentos de
              {{
                nome(origem())
              }}
              que podem ser copiados para
              {{
                nome(destino())
              }}
            </caption>
            <thead>
              <tr>
                <th scope="col"><span class="sr-only">Copiar</span></th>
                <th scope="col">Dia</th>
                <th scope="col">Movimento</th>
                <th scope="col">Categoria</th>
                <th scope="col" class="num">Valor</th>
              </tr>
            </thead>
            <tbody>
              @for (c of candidatos(); track chave(c)) {
                <tr>
                  <td>
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        class="cursor-pointer"
                        [checked]="marcados().has(chave(c))"
                        [disabled]="c.already_there"
                        (change)="alternar(c, $any($event.target).checked)"
                        [attr.aria-label]="'Copiar ' + c.description"
                      />
                      @if (c.already_there) {
                        <span class="fi-caption text-ink-3">já está lá</span>
                      }
                    </label>
                  </td>
                  <td class="num">{{ dia(c.due_on) }}</td>
                  <td class="text-ink">{{ c.description }}</td>
                  <td class="text-ink-2">
                    {{ rotuloDaCategoria(c) }}
                    @if (!c.repeats && !c.already_there) {
                      <span class="fi-caption text-ink-3">· não repete todo mês</span>
                    }
                  </td>
                  <td
                    class="num"
                    [class.text-up]="c.kind === 'income'"
                    [class.text-down]="c.kind === 'expense'"
                  >
                    {{ c.kind === 'income' ? '+' : '−' }}{{ reais(c.amount) }}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        @if (erroAoGravar()) {
          <p class="fi-caption text-adverse m-0 mt-4" role="alert">{{ erroAoGravar() }}</p>
        }

        <div class="flex items-center gap-3 mt-5 flex-wrap">
          <button
            type="button"
            class="btn-primary"
            (click)="copiar()"
            [disabled]="gravando() || marcados().size === 0"
          >
            <lucide-icon name="copy" size="16" aria-hidden="true"></lucide-icon>
            {{ gravando() ? 'Copiando…' : rotuloDoBotao() }}
          </button>
          <a
            [routerLink]="['/mes']"
            [queryParams]="{ mes: destino() === atual ? null : destino() }"
            class="btn-secondary no-underline"
          >
            Cancelar
          </a>
        </div>
      </section>
    }
  `,
})
export class MonthTemplateComponent implements OnInit {
  readonly nome = nomeDoMes;
  readonly atual = mesCorrente();

  private readonly api = inject(CashflowService);
  private readonly rota = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly molde = signal<CashMonthTemplate | null>(null);
  readonly marcados = signal<Set<string>>(new Set());
  readonly carregando = signal(true);
  readonly gravando = signal(false);
  readonly erro = signal('');
  readonly erroAoGravar = signal('');

  readonly destino = computed(() => this.molde()?.target ?? this.atual);
  readonly origem = computed(() => this.molde()?.source ?? '');
  readonly candidatos = computed(() => this.molde()?.candidates ?? []);

  readonly pergunta = computed(() => {
    const m = this.molde();
    return m ? `O que de ${nomeDoMes(m.source)} volta em ${nomeDoMes(m.target)}?` : 'O que repete?';
  });

  ngOnInit(): void {
    this.rota.queryParamMap.subscribe(params => {
      this.carregar(params.get('mes') ?? this.atual, params.get('de') ?? undefined);
    });
  }

  carregar(destino: string, origem?: string): void {
    this.carregando.set(true);
    this.erro.set('');

    this.api.monthTemplate(destino, origem).subscribe({
      next: m => {
        this.molde.set(m);
        this.marcados.set(
          new Set(m.candidates.filter(c => c.repeats && !c.already_there).map(c => this.chave(c)))
        );
        this.carregando.set(false);
      },
      error: resposta => {
        this.erro.set(resposta?.error?.detail ?? 'Tente de novo em alguns instantes.');
        this.carregando.set(false);
      },
    });
  }

  chave(c: CashTemplateCandidate): string {
    return `${c.kind}:${c.category}:${c.description}:${c.due_on}`;
  }

  alternar(c: CashTemplateCandidate, marcado: boolean): void {
    const proximos = new Set(this.marcados());
    if (marcado) proximos.add(this.chave(c));
    else proximos.delete(this.chave(c));
    this.marcados.set(proximos);
  }

  rotuloDoBotao(): string {
    const n = this.marcados().size;
    return n === 1 ? 'Copiar 1 lançamento' : `Copiar ${n} lançamentos`;
  }

  copiar(): void {
    const escolhidos = this.candidatos().filter(c => this.marcados().has(this.chave(c)));
    if (escolhidos.length === 0 || this.gravando()) return;

    this.gravando.set(true);
    this.erroAoGravar.set('');

    const destino = this.destino();
    this.api
      .addEntries(
        escolhidos.map(c => ({
          kind: c.kind,
          category: c.category,
          description: c.description,
          amount: c.amount,
          due_on: c.due_on,
          paid_on: null,
        }))
      )
      .subscribe({
        next: () => {
          this.gravando.set(false);
          void this.router.navigate(['/mes'], {
            queryParams: { mes: destino === this.atual ? null : destino },
          });
        },
        error: resposta => {
          this.gravando.set(false);
          this.erroAoGravar.set(
            resposta?.error?.detail ?? 'Não consegui copiar agora. Nada foi gravado.'
          );
        },
      });
  }

  rotuloDaCategoria(c: CashTemplateCandidate): string {
    const mapa = c.kind === 'income' ? fiCategoriasDeEntrada : fiCategoriasDeDespesa;
    return mapa[c.category]?.label ?? c.category;
  }

  dia(data: string): string {
    return data.slice(8, 10);
  }

  reais(valor: number): string {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
    });
  }
}
