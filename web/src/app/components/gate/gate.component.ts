import { CommonModule } from '@angular/common';
import { Component, computed, inject, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { EntitlementService } from '../../core';

/**
 * O gate contextual.
 *
 * Três regras que o componente **garante**, e não recomenda:
 *
 * 1. **Nunca desfoca dado do usuário.** Borrar saldo, P&L ou composição é
 *    hostil: é pegar o que já é da pessoa e escondê-lo até ela pagar. O que se
 *    esconde é projeção e sugestão — o que o produto acrescenta —, nunca o
 *    retrato do que é dela. Por isso o gate **substitui** um bloco, e não o
 *    cobre: não existe caminho no código em que ele fique por cima de conteúdo.
 *
 * 2. **A prévia é o argumento.** Quando quem chama sabe nomear o desvio real da
 *    carteira — "sua maior distância da meta é em FIIs: 8,4 pontos abaixo" —
 *    esse número é a melhor propaganda que existe, e é verdadeiro. Um gate que
 *    só diz "assine para ver" desperdiça a única coisa que o produto tem de
 *    diferente.
 *
 * 3. **Régua desligada, gate invisível.** Nunca um botão que não faz nada.
 *
 * A ordem de aparição é responsabilidade de quem usa o componente, mas há
 * teste do lado do backend: nenhum gate é alcançável antes de a pessoa ter
 * carteira, porque as rotas cercadas não existem sem ela.
 */
@Component({
  selector: 'app-gate',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    @if (visible()) {
      <section
        class="p-5 rounded-xl border border-hairline bg-ground-1"
        role="region"
        [attr.aria-label]="'Recurso do plano Premium: ' + title()"
      >
        <h3 class="flex items-center gap-2 text-base font-bold m-0 mb-1 text-ink">
          <lucide-icon name="lock" size="16" aria-hidden="true"></lucide-icon>
          {{ title() }}
        </h3>

        @if (preview()) {
          <p class="text-sm text-ink m-0 mb-2">{{ preview() }}</p>
        }

        <p class="text-sm text-ink-2 m-0 max-w-prose">{{ reason() }}</p>

        @if (limitReached()) {
          <p class="text-xs text-ink-3 m-0 mt-2">
            O teto reinicia no começo do mês. Ativos da sua carteira nunca contam.
          </p>
        }

        <div class="flex flex-wrap items-center gap-3 mt-4">
          <a class="btn-primary" routerLink="/voce/plano" (click)="upgrade.emit()">
            Ver o plano Premium
          </a>
          @if (secondaryLabel()) {
            <span class="text-sm text-ink-3">{{ secondaryLabel() }}</span>
          }
        </div>
      </section>
    }
  `,
})
export class GateComponent {
  private readonly entitlements = inject(EntitlementService);

  readonly feature = input.required<string>();
  readonly title = input('Disponível no Premium');

  /**
   * O número verdadeiro da carteira da pessoa, quando quem chama souber
   * calculá-lo sem a feature cercada.
   */
  readonly preview = input<string>('');
  readonly reason = input('Este recurso faz parte do plano Premium.');
  readonly limitReached = input(false);
  readonly secondaryLabel = input<string>('');

  readonly upgrade = output<void>();

  /** Some quando a régua está desligada ou quando a pessoa já tem direito. */
  readonly visible = computed(
    () => !this.entitlements.unrestricted() && !this.entitlements.allows(this.feature())
  );
}
