import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import {
  Directive,
  ElementRef,
  HostListener,
  Input,
  OnDestroy,
  PLATFORM_ID,
  inject,
} from '@angular/core';

/**
 * O comportamento de diálogo que seis superfícies faziam pela metade, ou não faziam.
 *
 * Quatro delas declaravam `role="dialog"` e `aria-modal="true"` e nenhuma
 * prendia o foco: Tab saía do diálogo para a página atrás, que não é inerte —
 * `aria-modal` prometia ao leitor de tela uma inércia que o DOM não tinha. E
 * nenhuma devolvia o foco ao elemento que a abriu, então fechar um modal
 * jogava o teclado no começo da página. Outras duas (o modal de alerta e o de
 * perfil) eram `div`s sobrepostas sem papel, sem foco inicial e sem Esc — e
 * passavam pelo lint porque ele cobra `aria-label` em botão de ícone, que elas
 * tinham.
 *
 * O que esta diretiva cobre: papel e modalidade, foco inicial no painel, ciclo
 * de Tab preso dentro dele, e devolução do foco ao fechar. O que ela não cobre:
 * inércia real do fundo para o cursor virtual do leitor de tela — isso exige
 * mover o diálogo para fora da árvore da aplicação, e está anotado como
 * pendência em vez de prometido aqui.
 */
@Directive({
  selector: '[fiDialog]',
  standalone: true,
})
export class DialogDirective implements OnDestroy {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly doc = inject(DOCUMENT);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  /** Nome acessível do diálogo. Ignorado se o template já declara aria-label. */
  @Input('fiDialog') label = '';

  private anterior: HTMLElement | null = null;

  constructor() {
    if (!this.isBrowser) return;

    const el = this.host.nativeElement;

    this.anterior = this.doc.activeElement as HTMLElement | null;

    if (!el.hasAttribute('role')) el.setAttribute('role', 'dialog');
    if (!el.hasAttribute('aria-modal')) el.setAttribute('aria-modal', 'true');
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
    if (this.label && !el.hasAttribute('aria-label') && !el.hasAttribute('aria-labelledby')) {
      el.setAttribute('aria-label', this.label);
    }

    // Microtask: o painel precisa estar no DOM e visível para receber foco.
    queueMicrotask(() => (this.focaveis()[0] ?? el).focus());
  }

  @HostListener('keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.key !== 'Tab') return;

    const focaveis = this.focaveis();
    if (focaveis.length === 0) {
      event.preventDefault();
      return;
    }

    const primeiro = focaveis[0];
    const ultimo = focaveis[focaveis.length - 1];
    const atual = this.doc.activeElement;

    if (event.shiftKey && (atual === primeiro || atual === this.host.nativeElement)) {
      event.preventDefault();
      ultimo.focus();
      return;
    }

    if (!event.shiftKey && atual === ultimo) {
      event.preventDefault();
      primeiro.focus();
    }
  }

  ngOnDestroy(): void {
    if (!this.isBrowser) return;

    /*
      A condição precisa cobrir o caso normal, que é o mais comum e era
      justamente o que falhava: quando o Angular remove o painel, o nó já saiu
      da árvore antes de `ngOnDestroy` rodar, e o foco cai no `<body>`. O teste
      `contains(activeElement)` dava falso aí, então fechar o drawer com Esc
      deixava o teclado no começo da página — exatamente o que a diretiva
      existe para evitar, e o que o comentário acima prometia resolver.

      Se o foco está num elemento concreto fora do diálogo, a pessoa clicou em
      outro lugar e roubá-lo de volta seria pior.
    */
    const foco = this.doc.activeElement;
    const perdido = !foco || foco === this.doc.body;

    if (perdido || this.host.nativeElement.contains(foco)) {
      this.anterior?.focus?.();
    }
  }

  private focaveis(): HTMLElement[] {
    const seletor = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled]):not([type="hidden"])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(',');

    return Array.from(this.host.nativeElement.querySelectorAll<HTMLElement>(seletor)).filter(
      el => el.offsetParent !== null || el === this.doc.activeElement
    );
  }
}
