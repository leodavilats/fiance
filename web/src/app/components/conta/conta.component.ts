import { CommonModule, DOCUMENT, isPlatformBrowser } from '@angular/common';
import { Component, inject, OnInit, PLATFORM_ID, signal } from '@angular/core';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService, DeletionPolicy, RecommendService } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-conta',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, PageHeaderComponent],
  templateUrl: './conta.component.html',
})
export class ContaComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly doc = inject(DOCUMENT);
  private readonly platformId = inject(PLATFORM_ID);

  readonly clearing = signal(false);
  readonly cacheMessage = signal('');

  readonly exporting = signal(false);
  readonly exportError = signal('');

  readonly policy = signal<DeletionPolicy | null>(null);
  readonly confirming = signal(false);
  readonly confirmText = signal('');
  readonly deleting = signal(false);
  readonly deleteError = signal('');

  ngOnInit(): void {
    this.svc.deletionPolicy().subscribe({
      next: p => this.policy.set(p),
      error: () => this.policy.set(null),
    });
  }

  /**
   * O arquivo chega como anexo; o navegador precisa de uma âncora para salvá-lo.
   *
   * A URL de objeto é revogada logo depois — sem isso o `Blob` fica preso na
   * memória da aba até o recarregamento.
   */
  exportarDados(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.exporting.set(true);
    this.exportError.set('');

    this.svc.exportAccount().subscribe({
      next: blob => {
        this.exporting.set(false);
        const url = URL.createObjectURL(blob);
        const link = this.doc.createElement('a');
        link.href = url;
        link.download = `fiance-${new Date().toISOString().slice(0, 10)}.json`;
        this.doc.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      },
      error: () => {
        this.exporting.set(false);
        this.exportError.set('Não conseguimos montar o arquivo agora. Tente de novo em instantes.');
      },
    });
  }

  /** A frase esperada vem do servidor; a tela não a inventa. */
  readonly frase = (): string => this.policy()?.confirmation_phrase ?? 'EXCLUIR';

  podeExcluir(): boolean {
    return this.confirmText().trim().toUpperCase() === this.frase().toUpperCase();
  }

  abrirConfirmacao(): void {
    this.confirming.set(true);
    this.confirmText.set('');
    this.deleteError.set('');
  }

  cancelarExclusao(): void {
    this.confirming.set(false);
    this.confirmText.set('');
  }

  excluirConta(): void {
    if (!this.podeExcluir()) return;

    this.deleting.set(true);
    this.deleteError.set('');

    this.svc.deleteAccount(this.frase()).subscribe({
      next: () => {
        void this.auth.logout();
        this.router.navigateByUrl('/login');
      },
      error: () => {
        this.deleting.set(false);
        this.deleteError.set('A exclusão não foi concluída. Sua conta continua como estava.');
      },
    });
  }

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
