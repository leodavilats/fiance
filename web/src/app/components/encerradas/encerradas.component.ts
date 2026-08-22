import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { CarteiraStore, UiHelperService } from '../../core';

@Component({
  selector: 'app-encerradas',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
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

  categoryLabel(category: string): string {
    return this.ui.categoryLabel(category);
  }
}
