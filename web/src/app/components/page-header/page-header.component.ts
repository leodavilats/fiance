import { Component, input } from '@angular/core';

@Component({
  selector: 'app-page-header',
  standalone: true,
  template: `
    <div class="mb-5">
      <h1 class="fi-title text-ink m-0" tabindex="-1">{{ title() }}</h1>

      @if (question()) {
        <p class="fi-body text-ink-2 m-0 mt-1 max-w-reading">{{ question() }}</p>
      }

      @if (scope()) {
        <p class="fi-caption text-ink-3 m-0 mt-1">{{ scope() }}</p>
      }

      <ng-content />
    </div>
  `,
})
export class PageHeaderComponent {
  readonly title = input.required<string>();

  readonly question = input<string>('');

  readonly scope = input<string>('');
}
