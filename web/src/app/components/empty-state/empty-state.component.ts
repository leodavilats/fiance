import { Component, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <div class="empty-state">
      <lucide-icon [name]="icon()" size="40"></lucide-icon>
      <h3>{{ title() }}</h3>
      <p>{{ description() }}</p>
      @if (actionLabel()) {
        <ng-content />
      }
    </div>
  `,
})
export class EmptyStateComponent {
  icon = input<string>('inbox');
  title = input<string>('Nenhum item encontrado');
  description = input<string>('');
  actionLabel = input<string>('');
}
