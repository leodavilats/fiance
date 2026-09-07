import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { OnboardingState, RecommendService } from '../../core';

interface Passo {
  readonly numero: number;
  readonly titulo: string;
  readonly descricao: string;
  readonly acaoLabel: string;
  readonly acaoRota: string;
  readonly icone: string;
}

const PASSOS: readonly Passo[] = [
  {
    numero: 1,
    titulo: 'Sua conta está pronta',
    descricao:
      'Nada aqui é obrigatório. Você pode pular a qualquer momento e ver o produto funcionando ' +
      'sobre uma carteira de exemplo.',
    acaoLabel: 'Continuar',
    acaoRota: '',
    icone: 'circle-check',
  },
  {
    numero: 2,
    titulo: 'Registre sua carteira',
    descricao:
      'Digite uma posição, cole a lista ou suba o CSV da corretora. Com quatro ativos o sistema ' +
      'já consegue emitir uma leitura de risco.',
    acaoLabel: 'Importar operações',
    acaoRota: '/carteira/importar',
    icone: 'wallet',
  },
  {
    numero: 3,
    titulo: 'Defina uma meta',
    descricao:
      'Uma meta de alocação basta. É ela que transforma "como estou" em "o que faço" — sem ela ' +
      'não há desvio a apontar.',
    acaoLabel: 'Definir metas',
    acaoRota: '/estrategia',
    icone: 'target',
  },
];

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="max-w-2xl mx-auto mt-8 px-4">
      <div class="flex items-center justify-between mb-6">
        <span class="fi-body text-ink-2"> Passo {{ passoAtual() }} de {{ passos.length }} </span>
        <button
          type="button"
          class="btn-quiet"
          [disabled]="finalizando()"
          [title]="finalizando() ? 'Concluindo…' : ''"
          (click)="concluir(true)"
        >
          Pular e ver um exemplo
        </button>
      </div>

      <div
        class="h-1 rounded-pill bg-hairline-strong mb-8 overflow-hidden"
        role="progressbar"
        [attr.aria-valuenow]="passoAtual()"
        aria-valuemin="1"
        [attr.aria-valuemax]="passos.length"
        [attr.aria-label]="'Progresso do onboarding'"
      >
        <div
          class="h-full bg-brand transition-[width] duration-base ease-enter"
          [style.width.%]="progresso()"
        ></div>
      </div>

      <div class="card">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-md bg-ground-2 text-brand shrink-0">
            <lucide-icon [name]="passo().icone" size="24"></lucide-icon>
          </div>
          <div class="min-w-0">
            <h1 class="fi-page-title m-0 mb-2 text-ink">{{ passo().titulo }}</h1>
            <p class="fi-body text-ink-2 m-0">{{ passo().descricao }}</p>

            @if (passoConcluido() && passoAtual() > 1) {
              <p class="fi-body flex items-center gap-2 text-favorable m-0 mt-3">
                <lucide-icon name="circle-check" size="16"></lucide-icon>
                Já está feito.
              </p>
            } @else if (estado(); as e) {
              <p class="fi-body text-ink-3 m-0 mt-3">{{ e.reason }}</p>
            }
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3 mt-6">
          @if (passoAtual() > 1) {
            <button type="button" class="btn-secondary" (click)="anterior()">Voltar</button>
          }

          @if (passo().acaoRota) {
            <a class="btn-secondary" [routerLink]="passo().acaoRota">
              {{ passo().acaoLabel }}
            </a>
          }

          <button
            type="button"
            class="btn-primary"
            [disabled]="finalizando()"
            [title]="finalizando() ? 'Concluindo…' : ''"
            (click)="proximo()"
          >
            @if (passoAtual() >= passos.length) {
              Concluir
            } @else {
              Continuar
            }
          </button>
        </div>
      </div>

      <p class="fi-caption text-ink-3 text-center mt-6">
        Nenhum passo é obrigatório. O produto funciona a partir de agora — pular só significa que
        você verá a análise sobre uma carteira de exemplo até cadastrar a sua.
      </p>
    </div>
  `,
})
export class OnboardingComponent implements OnInit {
  private readonly api = inject(RecommendService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly passos = PASSOS;
  readonly estado = signal<OnboardingState | null>(null);
  readonly finalizando = signal(false);

  readonly passoAtual = computed(() => {
    const daUrl = Number(this.route.snapshot.queryParamMap.get('passo'));
    if (daUrl >= 1 && daUrl <= PASSOS.length) return daUrl;
    return this.estado()?.step ?? 1;
  });

  readonly passo = computed(
    () => this.passos.find(p => p.numero === this.passoAtual()) ?? this.passos[0]
  );

  readonly passoConcluido = computed(() => {
    const estado = this.estado();
    if (!estado) return false;
    const numero = this.passoAtual();
    if (numero === 1) return true;
    if (numero === 2) return estado.positions > 0;
    return estado.has_goals;
  });

  readonly progresso = computed(() => (this.passoAtual() / PASSOS.length) * 100);

  ngOnInit(): void {
    this.api.getOnboarding().subscribe({
      next: estado => {
        this.estado.set(estado);
        if (!this.route.snapshot.queryParamMap.has('passo')) {
          void this.irPara(estado.step);
        }
      },
      error: () => this.estado.set(null),
    });
  }

  irPara(numero: number): Promise<boolean> {
    const alvo = Math.min(Math.max(numero, 1), PASSOS.length);
    return this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { passo: alvo },
      queryParamsHandling: 'merge',
    });
  }

  proximo(): void {
    if (this.passoAtual() >= PASSOS.length) {
      this.concluir(false);
      return;
    }
    void this.irPara(this.passoAtual() + 1);
  }

  anterior(): void {
    void this.irPara(this.passoAtual() - 1);
  }

  concluir(pulou: boolean): void {
    this.finalizando.set(true);
    this.api.completeOnboarding(pulou).subscribe({
      next: () => void this.router.navigateByUrl('/hoje'),
      error: () => {
        this.finalizando.set(false);
        void this.router.navigateByUrl('/hoje');
      },
    });
  }
}
