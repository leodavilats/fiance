import { CommonModule } from '@angular/common';
import { Component, input, output } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { DipAnalysisResponse } from '../../../core';

@Component({
  selector: 'app-dip-analysis-modal',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './dip-analysis-modal.component.html',
  styleUrls: ['./dip-analysis-modal.component.scss'],
})
export class DipAnalysisModalComponent {
  readonly analysis = input<DipAnalysisResponse | null>(null);
  readonly close = output<void>();

  closeAnalysis(): void {
    this.close.emit();
  }
}
