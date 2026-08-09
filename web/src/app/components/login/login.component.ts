import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, effect, inject, viewChild } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-[80vh] flex items-center justify-center">
      <div class="flex flex-col items-center gap-4 text-center max-w-sm">
        <div
          class="w-16 h-16 grid place-items-center rounded-2xl font-extrabold text-3xl text-[#0b0e14] bg-gradient-to-br from-accent to-accent-2"
        >
          f
        </div>
        <h1 class="text-2xl font-bold text-tx m-0">fianceAI</h1>
        <p class="text-muted m-0">Análise de investimentos B3 na sua mão</p>
        <div #googleButton class="mt-4"></div>
      </div>
    </div>
  `,
})
export class LoginComponent implements AfterViewInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly googleButton = viewChild.required<ElementRef<HTMLElement>>('googleButton');

  constructor() {
    effect(() => {
      if (this.auth.user()) {
        this.router.navigateByUrl('/dashboard');
      }
    });
  }

  ngAfterViewInit(): void {
    this.auth.renderGoogleButton(this.googleButton().nativeElement);
  }
}
