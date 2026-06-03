import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, effect, Renderer2 } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  DipAnalysisResponse,
  DipScannerResponse,
  LoadingService,
  RecommendService,
  UiHelperService,
} from '../../core';

interface DipScanForm {
  min_score: FormControl<number>;
  top: FormControl<number>;
  universe: FormControl<string>;
  category: FormControl<string>;
}

@Component({
  selector: 'app-dip',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './dip.component.html',
})
export class DipComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  private renderer = inject(Renderer2);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  constructor() {
    effect(() => {
      if (this.showPanel()) {
        this.renderer.addClass(document.body, 'overflow-hidden');
      } else {
        this.renderer.removeClass(document.body, 'overflow-hidden');
      }
    });
  }

  scanResult = signal<DipScannerResponse | null>(null);

  showPanel = signal(false);
  panelResult = signal<DipAnalysisResponse | null>(null);

  scanForm: FormGroup<DipScanForm> = this.fb.group({
    min_score: this.fb.control(42, { nonNullable: true }),
    top: this.fb.control(12, { nonNullable: true }),
    universe: this.fb.control('', { nonNullable: true }),
    category: this.fb.control('', { nonNullable: true }),
  });

  ngOnInit(): void {}

  submitScan(): void {
    const { min_score, top, universe, category } = this.scanForm.getRawValue();
    this.svc.dipScanner(min_score, top, universe || undefined, category || undefined).subscribe({
      next: res => {
        this.scanResult.set(res);
      },
      error: () => {},
      complete: () => {},
    });
  }

  openPanel(symbol: string): void {
    this.showPanel.set(true);
    this.panelResult.set(null);

    this.svc.dipAnalysis(symbol).subscribe({
      next: res => {
        this.panelResult.set(res);
      },
      error: () => {
        this.closePanel();
      },
    });
  }

  closePanel(): void {
    this.showPanel.set(false);
    this.panelResult.set(null);
  }
}
