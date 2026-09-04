import { CommonModule, DOCUMENT } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { ReferralService } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-referral',
  standalone: true,
  imports: [PageHeaderComponent, CommonModule, LucideAngularModule],
  templateUrl: './referral.component.html',
})
export class ReferralComponent implements OnInit {
  private readonly doc = inject(DOCUMENT);
  readonly referral = inject(ReferralService);

  readonly copiado = signal(false);

  ngOnInit(): void {
    this.referral.load();
  }

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
