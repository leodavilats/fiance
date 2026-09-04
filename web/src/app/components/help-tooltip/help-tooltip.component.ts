import { Component, computed, input, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

let contador = 0;

/**
 * A explicação de um termo, alcançável por teclado e por toque.
 *
 * A versão anterior abria só em `group-hover`: sem foco, sem `tabindex`, sem
 * `aria-describedby`. Nos sete lugares em que aparece — incluindo "DY" e
 * "Margem de segurança" em Descobrir — o glossário era invisível para quem
 * navega por teclado e para qualquer aparelho sem ponteiro. Num produto cuja
 * tese é explicabilidade, a explicação inalcançável é pior que a ausente:
 * parece resolvida.
 *
 * Agora é um `<button>` de verdade. Abre no foco e no clique, fecha em `Esc` e
 * ao sair, e o texto é anunciado pelo leitor de tela via `aria-describedby`. A
 * camada é `z-popover`, não `z-50` — que ficava abaixo do cabeçalho fixo.
 */
@Component({
  selector: 'app-help-tooltip',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <span class="relative inline-flex items-center ml-1">
      <!-- controle-proprio: gatilho de 16px dentro de um rótulo; um .btn-icon de
           36px empurraria a linha de texto inteira -->
      <button
        type="button"
        class="fi-focusable inline-flex items-center rounded-sm text-ink-2 hover:text-ink cursor-help"
        [attr.aria-label]="'O que significa ' + term()"
        [attr.aria-describedby]="aberto() ? id : null"
        [attr.aria-expanded]="aberto()"
        (click)="alternar()"
        (focus)="abrir()"
        (blur)="fechar()"
        (mouseenter)="abrir()"
        (mouseleave)="fechar()"
        (keydown.escape)="fechar()"
      >
        <lucide-icon name="circle-question-mark" size="12" aria-hidden="true"></lucide-icon>
      </button>

      @if (aberto()) {
        <span
          [id]="id"
          role="tooltip"
          class="fi-caption pointer-events-none absolute bottom-full left-1/2 z-popover mb-2 w-56 -translate-x-1/2 rounded-lg border border-hairline bg-ground-1 px-3 py-2 text-ink shadow-popover leading-relaxed"
        >
          {{ text() }}
        </span>
      }
    </span>
  `,
})
export class HelpTooltipComponent {
  readonly text = input.required<string>();
  /** O termo explicado, para o nome acessível do gatilho. */
  readonly term = input<string>('este termo');

  readonly id = `fi-tooltip-${++contador}`;
  private readonly visivel = signal(false);

  readonly aberto = computed(() => this.visivel());

  abrir(): void {
    this.visivel.set(true);
  }

  fechar(): void {
    this.visivel.set(false);
  }

  alternar(): void {
    this.visivel.update(v => !v);
  }
}
