import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, ElementRef, effect, inject, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core';
import { LogoComponent } from '../logo/logo.component';
import { WordmarkComponent } from '../logo/wordmark.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, LogoComponent, WordmarkComponent, RouterLink],
  template: `
    <div class="min-h-[80vh] flex items-center justify-center">
      <div class="flex flex-col items-center gap-4 text-center max-w-sm">
        <app-logo [size]="64" />
        <h1 class="m-0"><app-wordmark [height]="28" /></h1>
        <p class="fi-body text-ink-2 m-0">
          Preço justo, score e carteira — ações, FIIs, BDRs, ETFs e renda fixa da B3.
        </p>
        <div #googleButton class="mt-4"></div>

        <p class="fi-caption text-ink-3 m-0 mt-6">
          Ao entrar você aceita os
          <a routerLink="/termos" class="btn-link">Termos de Uso</a> e a
          <a routerLink="/privacidade" class="btn-link">Política de Privacidade</a>. O fiance é
          ferramenta de análise, não consultoria — veja o
          <a routerLink="/aviso-cvm" class="btn-link">Aviso CVM</a>. Não há garantia de retorno.
        </p>
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
        this.router.navigateByUrl('/mes');
      }
    });
  }

  ngAfterViewInit(): void {
    this.auth.renderGoogleButton(this.googleButton().nativeElement);
  }
}
