import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { LoadingService } from '../../core';

@Component({
  selector: 'app-global-loader',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    @if (loading.loading()) {
      <div class="fixed inset-0 fi-overlay z-loader flex items-center justify-center">
        <div
          class="flex flex-col items-center gap-3 p-6 rounded-lg bg-ground-1 border border-hairline shadow-popover"
        >
          <lucide-icon name="loader-circle" size="32" class="animate-spin text-brand"></lucide-icon>
          <p class="fi-label text-ink">Carregando...</p>
        </div>
      </div>
    }
  `,
  styleUrls: ['./global-loader.component.scss'],
})
export class GlobalLoaderComponent {
  readonly loading = inject(LoadingService);
}
