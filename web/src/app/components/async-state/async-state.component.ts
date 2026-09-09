import { Component, computed, input, output } from '@angular/core';
import { detalheUtil, mensagemDeErro } from '../../core/error-message';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { SkeletonComponent, SkeletonShape } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-async-state',
  standalone: true,
  imports: [EmptyStateComponent, SkeletonComponent],
  template: `
    @if (loading()) {
      <div class="py-2" role="status" [attr.aria-label]="rotuloDeEspera()">
        <app-skeleton [shape]="loadingShape()" [count]="loadingCount()" />
      </div>
    } @else if (error()) {
      <!-- design-exception: veredito — a frase de falha é a conclusão do sistema sobre a tentativa, não o nome de uma seção -->
      <div class="py-8 px-1 max-w-reading" role="alert">
        <h2 class="fi-verdict-sm text-ink m-0 mb-1">{{ errorTitle() }}</h2>
        <p class="fi-body text-ink-2 m-0">{{ frase() }}</p>
        @if (detalhe(); as extra) {
          <p class="fi-caption text-ink-3 m-0 mt-1">{{ extra }}</p>
        }
        <div class="flex flex-wrap items-center gap-3 mt-4">
          <button type="button" class="btn-primary" (click)="retry.emit()">Tentar de novo</button>
        </div>
      </div>
    } @else if (empty()) {
      <app-empty-state
        [title]="emptyTitle()"
        [reason]="emptyReason()"
        [nextStep]="emptyNextStep()"
        [actionLabel]="emptyActionLabel()"
        [actionRoute]="emptyActionRoute()"
        [secondaryLabel]="emptySecondaryLabel()"
        [secondaryRoute]="emptySecondaryRoute()"
        (action)="emptyAction.emit()"
      />
    } @else {
      <ng-content />
    }
  `,
})
export class AsyncStateComponent {
  readonly loading = input(false);

  /** O erro capturado, não a frase: quem decide a frase é `mensagemDeErro`. */
  readonly error = input<unknown>(null);

  readonly empty = input(false);

  readonly loadingShape = input<SkeletonShape>('row');
  readonly loadingCount = input(4);
  readonly loadingLabel = input<string>('');

  readonly errorTitle = input<string>('Algo não carregou');

  /** Completa "Não conseguimos ___ agora": "carregar suas posições". */
  readonly errorAction = input<string>('');

  readonly emptyTitle = input<string>('');
  readonly emptyReason = input<string>('');
  readonly emptyNextStep = input<string>('');
  readonly emptyActionLabel = input<string>('');
  readonly emptyActionRoute = input<string | null>(null);
  readonly emptySecondaryLabel = input<string>('');
  readonly emptySecondaryRoute = input<string | null>(null);

  readonly retry = output<void>();
  readonly emptyAction = output<void>();

  protected readonly frase = computed(() =>
    mensagemDeErro(this.error(), this.errorAction() || undefined)
  );

  protected readonly detalhe = computed(() => {
    const extra = detalheUtil(this.error());
    return extra && extra !== this.frase() ? extra : null;
  });

  protected readonly rotuloDeEspera = computed(
    () => this.loadingLabel() || 'Carregando estas informações'
  );
}
