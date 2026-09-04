import { CommonModule } from '@angular/common';
import { ProvenanceComponent } from '../../provenance/provenance.component';
import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  input,
  output,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { DialogDirective, DipAnalysisResponse } from '../../../core';
import { DipDiagnosisComponent } from '../../dip-diagnosis/dip-diagnosis.component';

@Component({
  selector: 'app-dip-analysis-modal',
  standalone: true,
  imports: [
    CommonModule,
    DialogDirective,
    DipDiagnosisComponent,
    LucideAngularModule,
    RouterLink,
    ProvenanceComponent,
  ],
  templateUrl: './dip-analysis-modal.component.html',
})
export class DipAnalysisModalComponent implements AfterViewInit, OnDestroy {
  readonly analysis = input<DipAnalysisResponse | null>(null);
  readonly close = output<void>();

  private readonly panel = viewChild<ElementRef<HTMLElement>>('panel');
  private readonly openedFrom = document.activeElement as HTMLElement | null;

  ngAfterViewInit(): void {
    this.panel()?.nativeElement.focus();
  }

  ngOnDestroy(): void {
    this.openedFrom?.focus?.();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.closeAnalysis();
  }

  closeAnalysis(): void {
    this.close.emit();
  }

  marginPct(a: DipAnalysisResponse): number | null {
    const m = a.fair_price?.margin_of_safety;
    return m == null ? null : m * 100;
  }
}
