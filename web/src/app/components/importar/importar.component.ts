import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { ImportPreview, RecommendService, SnackbarService, TransactionKind } from '../../core';

const KIND_LABEL: Record<TransactionKind, string> = {
  buy: 'Compra',
  sell: 'Venda',
  split: 'Desdobramento',
  bonus: 'Bonificação',
  transfer_in: 'Transferência de entrada',
  transfer_out: 'Transferência de saída',
  amortization: 'Amortização',
  adjust: 'Estado declarado',
};

/** Um arquivo maior que isso é engano, não carteira. */
const MAX_FILE_BYTES = 2 * 1024 * 1024;

@Component({
  selector: 'app-importar',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './importar.component.html',
})
export class ImportarComponent {
  private readonly api = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);
  private readonly router = inject(Router);

  readonly content = signal('');
  readonly preview = signal<ImportPreview | null>(null);
  readonly checking = signal(false);
  readonly importing = signal(false);

  /**
   * Repetida entra ou não. O padrão é não — reimportar a mesma nota é o erro
   * mais comum — mas duas compras iguais no mesmo dia acontecem, então a
   * decisão fica com quem sabe o que aconteceu.
   */
  readonly includeDuplicates = signal(false);

  readonly hasContent = computed(() => this.content().trim().length > 0);

  readonly novas = computed(
    () => this.preview()?.rows.filter(row => row.duplicate_of === null) ?? []
  );
  readonly repetidas = computed(
    () => this.preview()?.rows.filter(row => row.duplicate_of !== null) ?? []
  );

  readonly aImportar = computed(
    () => this.novas().length + (this.includeDuplicates() ? this.repetidas().length : 0)
  );

  readonly podeImportar = computed(
    () => (this.preview()?.ok ?? false) && this.aImportar() > 0 && !this.importing()
  );

  kindLabel(kind: TransactionKind): string {
    return KIND_LABEL[kind] ?? kind;
  }

  onFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (file.size > MAX_FILE_BYTES) {
      this.snackbar.showError('Arquivo muito grande. Divida a exportação por ano.');
      input.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      this.content.set(String(reader.result ?? ''));
      this.check();
    };
    reader.onerror = () => this.snackbar.showError('Não consegui ler o arquivo.');
    reader.readAsText(file, 'utf-8');
    input.value = '';
  }

  /** Lê sem gravar. É a etapa que existe para a revisão acontecer. */
  check(): void {
    if (!this.hasContent()) return;

    this.checking.set(true);
    this.preview.set(null);
    this.api.previewImport(this.content()).subscribe({
      next: res => {
        this.preview.set(res);
        this.checking.set(false);
      },
      error: () => this.checking.set(false),
    });
  }

  commit(): void {
    if (!this.podeImportar()) return;

    this.importing.set(true);
    this.api.commitImport(this.content(), this.includeDuplicates()).subscribe({
      next: res => {
        this.importing.set(false);
        const parte =
          res.skipped_duplicates > 0
            ? ` ${res.skipped_duplicates} repetida(s) ficaram de fora.`
            : '';
        this.snackbar.showSuccess(`${res.imported} operação(ões) importadas.${parte}`);
        void this.router.navigateByUrl('/carteira/transacoes');
      },
      error: () => this.importing.set(false),
    });
  }

  clear(): void {
    this.content.set('');
    this.preview.set(null);
  }
}
