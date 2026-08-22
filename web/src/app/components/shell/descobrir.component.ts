import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { DipAnalysisService } from '../../core';
import { DipAnalysisModalComponent } from '../market/dip-analysis-modal/dip-analysis-modal.component';
import { SectionNavComponent, SectionNavItem } from './section-nav.component';

@Component({
  selector: 'app-descobrir',
  standalone: true,
  imports: [RouterOutlet, SectionNavComponent, DipAnalysisModalComponent],
  template: `
    <app-section-nav [items]="items" label="Descobrir" />
    <router-outlet />
    @if (dip.open()) {
      <app-dip-analysis-modal [analysis]="dip.analysis()" (close)="dip.close()" />
    }
  `,
})
export class DescobrirComponent {
  readonly dip = inject(DipAnalysisService);

  readonly items: readonly SectionNavItem[] = [
    { path: '/descobrir/oportunidades', label: 'Oportunidades', icon: 'compass' },
    { path: '/descobrir/quedas', label: 'Quedas', icon: 'trending-down' },
    { path: '/descobrir/comparar', label: 'Comparar', icon: 'git-compare' },
  ];
}
