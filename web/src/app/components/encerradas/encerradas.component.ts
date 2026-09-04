import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { CarteiraStore, UiHelperService } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-encerradas',
  standalone: true,
  imports: [PageHeaderComponent, CommonModule, LucideAngularModule],
  templateUrl: './encerradas.component.html',
})
export class EncerradasComponent implements OnInit {
  private readonly store = inject(CarteiraStore);
  readonly ui = inject(UiHelperService);

  readonly closedTrades = this.store.closedTrades;
  readonly showClosedTrades = signal(true);

  ngOnInit(): void {
    this.store.ensureLoaded();
  }

  /** O sinal vive no texto, então o número entra sem ele. */
  absoluto(valor: number): number {
    return Math.abs(valor);
  }

  categoryLabel(category: string): string {
    return this.ui.categoryLabel(category);
  }
}
