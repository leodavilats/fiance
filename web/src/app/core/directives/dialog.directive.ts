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

@Directive({
  selector: '[fiDialog]',
  standalone: true,
})
export class DialogDirective implements OnDestroy {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly doc = inject(DOCUMENT);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  @Input('fiDialog') label = '';

  @Input() fiDialogFocus: 'primeiro' | 'painel' = 'primeiro';

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

    queueMicrotask(() => {
      const alvo = this.fiDialogFocus === 'painel' ? el : (this.focaveis()[0] ?? el);
      alvo.focus();
    });
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
