import { CommonModule, DOCUMENT } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  inject,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { ActivityService } from '../../core';
import { ActivityFeedComponent } from './activity-feed.component';

/**
 * A camada de atividade: 600px à direita, Esc fecha, foco entra e volta.
 *
 * O conteúdo é o mesmo de `/hoje/atividade` — o drawer existe para ler o
 * histórico **sem sair da tela onde você estava**, que é justamente o motivo de
 * ele não ser um modal.
 */
@Component({
  selector: 'app-activity-drawer',
  standalone: true,
  imports: [ActivityFeedComponent, CommonModule, LucideAngularModule, RouterLink],
  template: `
    @if (activity.open()) {
      <div
        class="fixed inset-0 z-[200] fi-overlay"
        (click)="activity.hide()"
        aria-hidden="true"
      ></div>

      <div
        #panel
        class="fixed top-0 right-0 bottom-0 z-[201] w-full max-w-[600px] bg-ground-1 border-l border-hairline shadow-drawer overflow-y-auto fi-drawer-enter"
        role="dialog"
        aria-modal="true"
        aria-label="Atividade recente"
        tabindex="-1"
      >
        <header
          class="sticky top-0 bg-ground-1 border-b border-hairline px-5 py-4 flex items-start justify-between gap-4"
        >
          <div>
            <p class="fi-eyebrow text-ink-3 m-0">Atividade</p>
            <h2 class="fi-title text-ink m-0 mt-0.5">O que aconteceu</h2>
          </div>
          <button
            type="button"
            (click)="activity.hide()"
            class="shrink-0 w-11 h-11 grid place-items-center rounded-md text-ink-2 hover:bg-ground-2 transition-colors cursor-pointer bg-transparent border-0"
            aria-label="Fechar atividade"
          >
            <lucide-icon name="x" size="18"></lucide-icon>
          </button>
        </header>

        <div class="px-5 py-5">
          <app-activity-feed />

          <a
            routerLink="/hoje/atividade"
            class="btn-secondary no-underline mt-6 w-full"
            (click)="activity.hide()"
          >
            Abrir em página inteira
          </a>
        </div>
      </div>
    }
  `,
})
export class ActivityDrawerComponent implements AfterViewInit, OnDestroy {
  readonly activity = inject(ActivityService);

  private readonly doc = inject(DOCUMENT);

  private readonly panel = viewChild<ElementRef<HTMLElement>>('panel');
  private openedFrom: HTMLElement | null = null;

  ngAfterViewInit(): void {
    this.openedFrom = this.doc.activeElement as HTMLElement | null;
    this.panel()?.nativeElement.focus();
  }

  ngOnDestroy(): void {
    this.openedFrom?.focus?.();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.activity.open()) this.activity.hide();
  }
}
