import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { RecommendService } from '../../core';

@Component({
  selector: 'app-conta',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './conta.component.html',
})
export class ContaComponent {
  private readonly svc = inject(RecommendService);

  readonly clearing = signal(false);
  readonly cacheMessage = signal('');

  clearAssetsCache(): void {
    this.clear('uasset:*');
  }

  clearAllCache(): void {
    this.clear('*');
  }

  private clear(pattern: string): void {
    this.clearing.set(true);
    this.cacheMessage.set('');
    this.svc.clearCache(pattern).subscribe({
      next: res => {
        this.clearing.set(false);
        this.cacheMessage.set(`✓ ${res.deleted} entradas removidas`);
        setTimeout(() => this.cacheMessage.set(''), 3000);
      },
      error: () => {
        this.clearing.set(false);
        this.cacheMessage.set('✗ Não conseguimos limpar o cache');
        setTimeout(() => this.cacheMessage.set(''), 4000);
      },
    });
  }
}
