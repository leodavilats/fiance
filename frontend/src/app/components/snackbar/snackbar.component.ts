import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { SnackbarService } from '../../core';

@Component({
  selector: 'app-snackbar',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      @for (msg of snackbar.messages(); track msg.id) {
        <div 
          class="flex items-center gap-3 p-4 rounded-lg shadow-lg border animate-slide-in"
          [class.bg-danger]="msg.type === 'error'"
          [class.bg-success]="msg.type === 'success'"
          [class.bg-info]="msg.type === 'info'"
          [class.border-danger]="msg.type === 'error'"
          [class.border-success]="msg.type === 'success'"
          [class.border-info]="msg.type === 'info'"
          [class.text-white]="true"
        >
          <lucide-icon 
            [name]="msg.type === 'error' ? 'circle-x' : msg.type === 'success' ? 'circle-check' : 'info'"
            size="20"
          ></lucide-icon>
          <p class="flex-1 m-0 text-sm font-medium">{{ msg.message }}</p>
          <button 
            type="button"
            class="w-6 h-6 grid place-items-center rounded hover:bg-white/20 transition-colors cursor-pointer bg-transparent border-0 text-white"
            (click)="snackbar.remove(msg.id)"
          >
            <lucide-icon name="x" size="16"></lucide-icon>
          </button>
        </div>
      }
    </div>
  `,
  styles: [`
    .bg-danger {
      background-color: rgb(239, 68, 68);
      border-color: rgb(220, 38, 38);
    }
    .bg-success {
      background-color: rgb(34, 197, 94);
      border-color: rgb(22, 163, 74);
    }
    .bg-info {
      background-color: rgb(59, 130, 246);
      border-color: rgb(37, 99, 235);
    }
    @keyframes slide-in {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    .animate-slide-in {
      animation: slide-in 0.3s ease-out;
    }
  `]
})
export class SnackbarComponent {
  readonly snackbar = inject(SnackbarService);
}
