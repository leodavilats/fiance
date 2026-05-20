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
      <div class="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center backdrop-blur-sm">
        <div class="flex flex-col items-center gap-3 p-6 rounded-xl bg-panel border border-border shadow-2xl">
          <lucide-icon name="loader-circle" size="32" class="animate-spin text-accent"></lucide-icon>
          <p class="text-tx font-medium">Carregando...</p>
        </div>
      </div>
    }
  `,
  styles: [`
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .animate-spin {
      animation: spin 1s linear infinite;
    }
  `]
})
export class GlobalLoaderComponent {
  readonly loading = inject(LoadingService);
}
