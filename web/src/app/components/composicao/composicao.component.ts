import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { CarteiraStore, UiHelperService } from '../../core';

@Component({
  selector: 'app-composicao',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './composicao.component.html',
})
export class ComposicaoComponent implements OnInit {
  private readonly store = inject(CarteiraStore);
  readonly ui = inject(UiHelperService);

  readonly isEmpty = this.store.isEmpty;
  readonly composicaoMode = this.store.composicaoMode;
  readonly composicaoSlices = this.store.composicaoSlices;
  readonly conicGradient = this.store.conicGradient;
  readonly alocacaoPorTipo = this.store.alocacaoPorTipo;
  readonly alocacaoPorSetor = this.store.alocacaoPorSetor;

  ngOnInit(): void {
    this.store.ensureLoaded();
  }

  setComposicaoMode(mode: 'ativo' | 'setor'): void {
    this.store.composicaoMode.set(mode);
  }
}
