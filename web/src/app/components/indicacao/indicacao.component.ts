import { CommonModule, DOCUMENT } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { ReferralService } from '../../core';

@Component({
  selector: 'app-indicacao',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './indicacao.component.html',
})
export class IndicacaoComponent implements OnInit {
  private readonly doc = inject(DOCUMENT);
  readonly referral = inject(ReferralService);

  readonly copiado = signal(false);

  ngOnInit(): void {
    this.referral.load();
  }

  /**
   * O link inteiro, não só o código.
   *
   * Quem recebe "use o código KQ7M2XPB" tem que descobrir onde digitá-lo; quem
   * recebe um link clica. A origem sai do documento porque este componente roda
   * também no Node durante o SSR.
   */
  link(code: string): string {
    const origem = this.doc.defaultView?.location.origin ?? '';
    return `${origem}/?indicacao=${code}`;
  }

  async copiar(code: string): Promise<void> {
    const texto = this.link(code);
    const area = this.doc.defaultView?.navigator?.clipboard;

    try {
      if (area) await area.writeText(texto);
      this.copiado.set(true);
      setTimeout(() => this.copiado.set(false), 2000);
    } catch {
      this.copiado.set(false);
    }
  }
}
