import { CommonModule } from '@angular/common';
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
import { DipAnalysisResponse } from '../../../core';
import { DipDiagnosisComponent } from '../../dip-diagnosis/dip-diagnosis.component';

/**
 * O drawer de "por que caiu".
 *
 * Antes era um modal com o score DIP em corpo 48 no centro e o breakdown numérico
 * logo abaixo — o número antes da pergunta. Agora o conteúdo é o `DipDiagnosis`,
 * e o drawer só cuida do que é comportamento de camada: Esc fecha, o foco entra
 * e volta para onde estava, e a lista continua visível atrás.
 */
@Component({
  selector: 'app-dip-analysis-modal',
  standalone: true,
  imports: [CommonModule, DipDiagnosisComponent, LucideAngularModule, RouterLink],
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

  /** O backend devolve a margem como fração; a régua lê percentual. */
  marginPct(a: DipAnalysisResponse): number | null {
    const m = a.fair_price?.margin_of_safety;
    return m == null ? null : m * 100;
  }
}
