import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CarteiraStore,
  PortfolioHealth,
  RecommendService,
  UiHelperService,
  fiHealthBands,
} from '../../core';
import { ScoreRulerComponent } from '../score-ruler/score-ruler.component';

interface HealthDimension {
  readonly label: string;
  readonly score: number;
  readonly explains: string;
}

const MIN_POSITIONS_FOR_HEALTH = 4;

@Component({
  selector: 'app-carteira-resumo',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink, ScoreRulerComponent],
  templateUrl: './carteira-resumo.component.html',
})
export class CarteiraResumoComponent implements OnInit {
  readonly store = inject(CarteiraStore);
  private readonly svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  readonly health = signal<PortfolioHealth | null>(null);
  readonly healthBands = fiHealthBands;
  readonly showHealthDetail = signal(false);

  ngOnInit(): void {
    this.store.ensureLoaded();
    this.svc.dashboard().subscribe({
      next: d => this.health.set(d.health),
      error: () => this.health.set(null),
    });
  }

  readonly healthReliable = computed(
    () => this.store.negociadosCount() >= MIN_POSITIONS_FOR_HEALTH
  );

  readonly healthDimensions = computed<HealthDimension[]>(() => {
    const h = this.health();
    if (!h) return [];
    return [
      {
        label: 'Concentração',
        score: h.concentration_score,
        explains: 'O quanto o seu maior ativo pesa no total da carteira.',
      },
      {
        label: 'Setor',
        score: h.sector_concentration_score,
        explains: 'O quanto as suas ações e BDRs dependem de um único setor.',
      },
      {
        label: 'Diversificação',
        score: h.diversification_score,
        explains: 'A variedade entre classes: renda fixa, ações, FIIs, BDRs e ETFs.',
      },
      {
        label: 'Risco',
        score: h.risk_score,
        explains: 'A fatia da carteira em ativos com sinal de venda.',
      },
    ];
  });

  readonly resultDirectionClass = computed(() => {
    const value = this.store.rendimentoTotal();
    if (value > 0) return 'text-up';
    if (value < 0) return 'text-down';
    return 'text-ink-2';
  });

  readonly absResult = computed(() => Math.abs(this.store.rendimentoTotal()));

  readonly gaps = computed(() =>
    this.store
      .alocacaoPorTipo()
      .filter(a => a.targetPct != null)
      .map(a => ({
        label: this.ui.categoryLabel(a.tipo),
        currentPct: a.pct,
        targetPct: a.targetPct as number,
        deltaPct: a.pct - (a.targetPct as number),
      }))
      .sort((a, b) => Math.abs(b.deltaPct) - Math.abs(a.deltaPct))
  );

  readonly hasGoals = computed(() => this.gaps().length > 0);

  toggleHealthDetail(): void {
    this.showHealthDetail.update(v => !v);
  }
}
