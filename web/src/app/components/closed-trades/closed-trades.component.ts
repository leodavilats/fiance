import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { CarteiraStore, UiHelperService } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-closed-trades',
  standalone: true,
  imports: [PageHeaderComponent, CommonModule, LucideAngularModule],
  templateUrl: './closed-trades.component.html',
})
export class ClosedTradesComponent implements OnInit {
  private readonly store = inject(CarteiraStore);
  readonly ui = inject(UiHelperService);

  readonly closedTrades = this.store.closedTrades;
  readonly showClosedTrades = signal(true);

  ngOnInit(): void {
    this.store.ensureLoaded();
  }

  absoluto(valor: number): number {
    return Math.abs(valor);
  }

  categoryLabel(category: string): string {
    return this.ui.categoryLabel(category);
  }
}
