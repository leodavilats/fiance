import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, effect, inject, viewChild } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core';
import { LogoComponent } from '../logo/logo.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, LogoComponent],
  template: `
    <div class="min-h-[80vh] flex items-center justify-center">
      <div class="flex flex-col items-center gap-4 text-center max-w-sm">
        <app-logo [size]="64" />
        <h1 class="fi-verdict text-ink m-0">fiance</h1>
        <p class="fi-body text-ink-2 m-0">
          Preço justo, score e carteira — ações, FIIs, BDRs, ETFs e renda fixa da B3.
        </p>
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
        this.router.navigateByUrl('/hoje');
      }
    });
  }

  ngAfterViewInit(): void {
    this.auth.renderGoogleButton(this.googleButton().nativeElement);
  }
}
