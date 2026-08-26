import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CarteiraStore, UiHelperService } from '../../core';
import { AllocationGapComponent } from '../allocation-gap/allocation-gap.component';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-composicao',
  standalone: true,
  imports: [
    AllocationGapComponent,
    CommonModule,
    EmptyStateComponent,
    RouterLink,
    SkeletonComponent,
  ],
  templateUrl: './composicao.component.html',
})
export class ComposicaoComponent implements OnInit {
  private readonly store = inject(CarteiraStore);
  readonly ui = inject(UiHelperService);

  readonly isEmpty = this.store.isEmpty;
  readonly composicaoMode = this.store.composicaoMode;
  readonly composicaoSlices = this.store.composicaoSlices;
  readonly alocacaoPorTipo = this.store.alocacaoPorTipo;
  readonly alocacaoPorSetor = this.store.alocacaoPorSetor;

  ngOnInit(): void {
    this.store.ensureLoaded();
  }

  setComposicaoMode(mode: 'ativo' | 'setor'): void {
    this.store.composicaoMode.set(mode);
  }

  /** A meta da fatia, quando existe. `null` some da leitura em vez de virar 0. */
  targetFor(label: string): number | null {
    return this.composicaoSlices().find(s => s.label === label)?.targetPct ?? null;
  }

  readonly hasAnyTarget = computed(() => this.composicaoSlices().some(s => s.targetPct != null));
}
