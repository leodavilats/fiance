import { NgTemplateOutlet } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

export interface SectionNavItem {
  readonly path: string;
  readonly label: string;
  readonly icon: string;

  /**
   * Nome do grupo, quando várias leituras são a mesma coisa vista de ângulos diferentes.
   *
   * `/patrimonio` tinha seis pares soltos, o que não é hierarquia — é uma lista. Posições,
   * Encerradas e Proventos são três leituras do **mesmo** razão, e agrupá-las diz uma verdade da
   * arquitetura em vez de esconder o número de itens. Itens do mesmo grupo ficam adjacentes.
   */
  readonly group?: string;
}

interface Bloco {
  readonly group: string | null;
  readonly items: readonly SectionNavItem[];
}

@Component({
  selector: 'app-section-nav',
  standalone: true,
  imports: [NgTemplateOutlet, RouterLink, RouterLinkActive, LucideAngularModule],
  template: `
    <div class="fi-section-shell">
      <nav class="fi-section-rail mb-5" [attr.aria-label]="'Seções de ' + label()">
        <ul
          class="flex flex-wrap items-center gap-1 list-none m-0 p-0 border-b border-hairline pb-2"
        >
          @for (bloco of blocos(); track $index) {
            @if (bloco.group) {
              <li class="flex items-center gap-2 ml-2 pl-3 border-l border-hairline">
                <span class="fi-eyebrow text-ink-3">{{ bloco.group }}</span>
                <ul class="flex flex-wrap gap-1 list-none m-0 p-0" [attr.aria-label]="bloco.group">
                  @for (item of bloco.items; track item.path) {
                    <li>
                      <ng-container
                        [ngTemplateOutlet]="pill"
                        [ngTemplateOutletContext]="{ item }"
                      />
                    </li>
                  }
                </ul>
              </li>
            } @else {
              @for (item of bloco.items; track item.path) {
                <li>
                  <ng-container [ngTemplateOutlet]="pill" [ngTemplateOutletContext]="{ item }" />
                </li>
              }
            }
          }
        </ul>
      </nav>
      <div class="fi-section-body">
        <ng-content />
      </div>
    </div>

    <ng-template #pill let-item="item">
      <a
        [routerLink]="item.path"
        routerLinkActive="active"
        #rla="routerLinkActive"
        [routerLinkActiveOptions]="{ exact: true }"
        [attr.aria-current]="rla.isActive ? 'page' : null"
        class="subtab-btn"
      >
        <lucide-icon [name]="item.icon" size="14"></lucide-icon>
        <span class="subtab-label">
          <span class="subtab-label-text">{{ item.label }}</span>
          <span class="subtab-label-sizer" aria-hidden="true">{{ item.label }}</span>
        </span>
      </a>
    </ng-template>
  `,
})
export class SectionNavComponent {
  readonly items = input.required<readonly SectionNavItem[]>();
  readonly label = input<string>('navegação');

  protected readonly blocos = computed<readonly Bloco[]>(() => {
    const blocos: Bloco[] = [];
    for (const item of this.items()) {
      const grupo = item.group ?? null;
      const ultimo = blocos[blocos.length - 1];
      if (ultimo && ultimo.group === grupo) {
        (ultimo.items as SectionNavItem[]).push(item);
      } else {
        blocos.push({ group: grupo, items: [item] });
      }
    }
    return blocos;
  });
}
