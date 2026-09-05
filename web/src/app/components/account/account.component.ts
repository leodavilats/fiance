import { CommonModule, DOCUMENT, isPlatformBrowser } from '@angular/common';
import { Component, inject, OnInit, PLATFORM_ID, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService, DeletionPolicy, RecommendService } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-account',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, PageHeaderComponent, RouterLink],
  template: `
    <app-page-header
      title="Conta e dados"
      question="O que é seu, como levá-lo embora e de onde vem cada número."
    />

    <div class="flex flex-col gap-8">
      <div class="fi-block">
        <h2 class="fi-title text-ink m-0 mb-1">Levar seus dados</h2>
        <p class="fi-body text-ink-2 m-0 mb-4 max-w-reading">
          Um arquivo JSON com carteira, lançamentos, renda fixa, proventos, metas e preferências —
          tudo o que está associado à sua conta, como o servidor o guarda. Não passa por plano.
        </p>
        <div class="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            class="btn-secondary"
            (click)="exportarDados()"
            [disabled]="exporting()"
          >
            <lucide-icon
              [name]="exporting() ? 'loader-circle' : 'download'"
              size="16"
              [class.spin]="exporting()"
            ></lucide-icon>
            {{ exporting() ? 'Montando o arquivo…' : 'Exportar meus dados' }}
          </button>
          @if (exportError()) {
            <span class="fi-body text-adverse" role="status">{{ exportError() }}</span>
          }
        </div>
      </div>

      <div class="fi-block">
        <h2 class="fi-title text-ink m-0 mb-1">Excluir a conta</h2>
        <p class="fi-body text-ink-2 m-0 mb-3 max-w-reading">
          A remoção é imediata no banco e não tem desfazer. Exporte antes se quiser guardar o
          histórico.
        </p>

        @if (policy(); as p) {
          <div class="notice notice-attention mb-4 max-w-reading">
            <lucide-icon
              name="triangle-alert"
              size="16"
              class="text-attention mt-0.5 shrink-0"
              aria-hidden="true"
            ></lucide-icon>
            <div class="min-w-0">
              <p class="fi-body text-ink m-0">
                Apaga <span class="fi-num">{{ p.removes.length }}</span> conjuntos de dados:
                {{ p.removes.join(', ') }}.
              </p>
              <p class="fi-caption text-ink-2 m-0 mt-1">{{ p.note }}</p>
              <p class="fi-caption text-ink-3 m-0 mt-1">
                Prazo declarado para backups e réplicas:
                <span class="fi-num">{{ p.sla_days }}</span> dias.
              </p>
            </div>
          </div>
        }

        @if (!confirming()) {
          <button type="button" class="btn-secondary text-adverse" (click)="abrirConfirmacao()">
            <lucide-icon name="trash2" size="16"></lucide-icon>
            Excluir minha conta
          </button>
        } @else {
          <div class="flex flex-col gap-3 max-w-reading">
            <div class="field">
              <label class="field-label" for="conta-confirmar">
                Para confirmar, escreva {{ frase() }}
              </label>
              <input
                id="conta-confirmar"
                type="text"
                class="input uppercase"
                autocomplete="off"
                [value]="confirmText()"
                (input)="confirmText.set($any($event.target).value)"
              />
              <span class="field-hint">
                A frase é exigida pelo servidor — a tela não consegue pular esta etapa.
              </span>
            </div>

            @if (deleteError()) {
              <p class="field-error m-0" role="alert">{{ deleteError() }}</p>
            }

            <div class="flex items-center gap-3 flex-wrap">
              <button
                type="button"
                class="btn-secondary text-adverse"
                [disabled]="!podeExcluir() || deleting()"
                (click)="excluirConta()"
              >
                <lucide-icon
                  [name]="deleting() ? 'loader-circle' : 'trash2'"
                  size="16"
                  [class.spin]="deleting()"
                ></lucide-icon>
                {{ deleting() ? 'Excluindo…' : 'Excluir definitivamente' }}
              </button>
              <button
                type="button"
                class="btn-quiet"
                (click)="cancelarExclusao()"
                [disabled]="deleting()"
                [title]="deleting() ? 'A exclusão já começou e não pode ser cancelada' : ''"
              >
                Cancelar
              </button>
            </div>
          </div>
        }
      </div>

      <div class="fi-block">
        <h2 class="fi-title text-ink m-0 mb-1">De onde vêm os dados</h2>
        <p class="fi-body text-ink-2 m-0 mb-5 max-w-reading">
          Num produto financeiro, a origem do número faz parte da informação.
        </p>
        <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5 m-0">
          <div>
            <dt class="fi-eyebrow text-ink-3 m-0 mb-1">Cotações e fundamentos</dt>
            <dd class="fi-body text-ink m-0">BRAPI — ações da B3, FIIs, BDRs e ETFs.</dd>
          </div>
          <div>
            <dt class="fi-eyebrow text-ink-3 m-0 mb-1">CDI, Selic e IPCA</dt>
            <dd class="fi-body text-ink m-0">
              Banco Central (séries SGS). Quando o BCB não responde, o app usa uma estimativa e
              sinaliza isso ao lado do número.
            </dd>
          </div>
          <div>
            <dt class="fi-eyebrow text-ink-3 m-0 mb-1">Preço justo</dt>
            <dd class="fi-body text-ink m-0">
              Bazin, Graham e fluxo de caixa descontado, aplicados conforme o tipo de ativo. Cada
              método aparece separado, com o insumo que usou.
            </dd>
          </div>
          <div>
            <dt class="fi-eyebrow text-ink-3 m-0 mb-1">Score</dt>
            <dd class="fi-body text-ink m-0">
              Margem de segurança, qualidade, endividamento, crescimento, dividendos e técnico,
              ponderados pelo seu perfil de risco. Com indicadores faltando, o score sai como “sem
              dado” em vez de nota baixa.
            </dd>
          </div>
        </dl>
        <p class="fi-caption text-ink-3 m-0 mt-5 pt-4 border-t border-hairline max-w-reading">
          Tudo o que o fiance mostra é estimativa a partir de dado público, para estudo da sua
          própria carteira. Não é recomendação de investimento e não há garantia de retorno.
        </p>
      </div>

      <div class="fi-block">
        <h2 class="fi-title text-ink m-0 mb-1">Cache de dados</h2>
        <p class="fi-body text-ink-2 m-0 mb-4 max-w-reading">
          As cotações ficam guardadas por um tempo para não pedir a mesma coisa à fonte a cada tela.
          Limpar força a próxima leitura a ir buscar de novo.
        </p>
        <div class="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            class="btn-secondary"
            (click)="clearAssetsCache()"
            [disabled]="clearing()"
          >
            <lucide-icon
              [name]="clearing() ? 'loader-circle' : 'refresh-cw'"
              size="16"
            ></lucide-icon>
            {{ clearing() ? 'Limpando…' : 'Limpar cache de ativos' }}
          </button>
          <button
            type="button"
            class="btn-secondary"
            (click)="clearAllCache()"
            [disabled]="clearing()"
          >
            <lucide-icon [name]="clearing() ? 'loader-circle' : 'trash2'" size="16"></lucide-icon>
            {{ clearing() ? 'Limpando…' : 'Limpar todo o cache' }}
          </button>
          @if (cacheMessage()) {
            <span class="fi-body text-ink-2" role="status">{{ cacheMessage() }}</span>
          }
        </div>
      </div>

      <div class="fi-block">
        <h2 class="fi-title text-ink m-0 mb-1">Termos, privacidade e a fronteira CVM</h2>
        <p class="fi-body text-ink-2 m-0 mb-4 max-w-reading">
          O que o fiance é, o que ele não é, que dado ele guarda e com quem compartilha. As três
          páginas abrem sem login — pode conferir antes de decidir ficar.
        </p>
        <ul class="fi-body m-0 pl-5 list-disc text-ink">
          <li><a routerLink="/termos" class="btn-link">Termos de Uso</a></li>
          <li><a routerLink="/privacidade" class="btn-link">Política de Privacidade</a></li>
          <li>
            <a routerLink="/aviso-cvm" class="btn-link">Aviso CVM</a> — por que a análise não é
            recomendação
          </li>
        </ul>
      </div>
    </div>
  `,
})
export class AccountComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly doc = inject(DOCUMENT);
  private readonly platformId = inject(PLATFORM_ID);

  readonly clearing = signal(false);
  readonly cacheMessage = signal('');

  readonly exporting = signal(false);
  readonly exportError = signal('');

  readonly policy = signal<DeletionPolicy | null>(null);
  readonly confirming = signal(false);
  readonly confirmText = signal('');
  readonly deleting = signal(false);
  readonly deleteError = signal('');

  ngOnInit(): void {
    this.svc.deletionPolicy().subscribe({
      next: p => this.policy.set(p),
      error: () => this.policy.set(null),
    });
  }

  exportarDados(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    this.exporting.set(true);
    this.exportError.set('');

    this.svc.exportAccount().subscribe({
      next: blob => {
        this.exporting.set(false);
        const url = URL.createObjectURL(blob);
        const link = this.doc.createElement('a');
        link.href = url;
        link.download = `fiance-${new Date().toISOString().slice(0, 10)}.json`;
        this.doc.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      },
      error: () => {
        this.exporting.set(false);
        this.exportError.set('Não conseguimos montar o arquivo agora. Tente de novo em instantes.');
      },
    });
  }

  readonly frase = (): string => this.policy()?.confirmation_phrase ?? 'EXCLUIR';

  podeExcluir(): boolean {
    return this.confirmText().trim().toUpperCase() === this.frase().toUpperCase();
  }

  abrirConfirmacao(): void {
    this.confirming.set(true);
    this.confirmText.set('');
    this.deleteError.set('');
  }

  cancelarExclusao(): void {
    this.confirming.set(false);
    this.confirmText.set('');
  }

  excluirConta(): void {
    if (!this.podeExcluir()) return;

    this.deleting.set(true);
    this.deleteError.set('');

    this.svc.deleteAccount(this.frase()).subscribe({
      next: () => {
        void this.auth.logout();
        this.router.navigateByUrl('/login');
      },
      error: () => {
        this.deleting.set(false);
        this.deleteError.set('A exclusão não foi concluída. Sua conta continua como estava.');
      },
    });
  }

  clearAssetsCache(): void {
    this.clear('uasset:*');
  }

  clearAllCache(): void {
    this.clear('*');
  }

  private clear(pattern: string): void {
    this.clearing.set(true);
    this.cacheMessage.set('');
    this.svc.clearCache(pattern).subscribe({
      next: res => {
        this.clearing.set(false);
        this.cacheMessage.set(`✓ ${res.deleted} entradas removidas`);
        setTimeout(() => this.cacheMessage.set(''), 3000);
      },
      error: () => {
        this.clearing.set(false);
        this.cacheMessage.set('✗ Não conseguimos limpar o cache');
        setTimeout(() => this.cacheMessage.set(''), 4000);
      },
    });
  }
}
