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
  templateUrl: './onboarding.component.html',
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
