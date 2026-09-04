import { Component, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

export interface SectionNavItem {
  readonly path: string;
  readonly label: string;
  readonly icon: string;
}

@Component({
  selector: 'app-section-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, LucideAngularModule],
  template: `
    <div class="fi-section-shell">
      <nav class="fi-section-rail mb-5" [attr.aria-label]="'Seções de ' + label()">
        <ul class="flex flex-wrap gap-1 list-none m-0 p-0 border-b border-hairline pb-2">
          @for (item of items(); track item.path) {
            <li>
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
            </li>
          }
        </ul>
      </nav>
      <div class="fi-section-body">
        <ng-content />
      </div>
    </div>
  `,
})
export class SectionNavComponent {
  readonly items = input.required<readonly SectionNavItem[]>();
  readonly label = input<string>('navegação');
}
