import { CommonModule } from '@angular/common';
import { Component, inject, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { DipScanItem, RecommendService } from '../../../core';

@Component({
  selector: 'app-dip-scanner',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './dip-scanner.component.html',
  styleUrls: ['./dip-scanner.component.scss'],
})
export class DipScannerComponent {
  private api = inject(RecommendService);
  private fb = inject(FormBuilder);

  readonly analyze = output<string>();

  readonly dipResults = signal<{ items: DipScanItem[] } | null>(null);

  scanForm = this.fb.nonNullable.group({
    min_score: [40, [Validators.required, Validators.min(0), Validators.max(100)]],
    top: [12, [Validators.required, Validators.min(1), Validators.max(30)]],
    category: [''],
  });

  runScan() {
    if (this.scanForm.invalid) return;
    const { min_score, top, category } = this.scanForm.getRawValue();
    this.api
      .dipScanner(min_score, top, undefined, category || undefined)
      .subscribe(data => this.dipResults.set(data));
  }

  showDipAnalysis(ticker: string) {
    this.analyze.emit(ticker);
  }
}
