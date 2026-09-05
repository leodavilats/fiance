import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { environment } from '../../../environments/environment';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { LegalDraftNoticeComponent } from './legal-draft-notice.component';

interface AffirmationMode {
  level: number;
  name: string;
  disclaimer: string;
  prescriptive: boolean;
  asset_level: boolean;
}

@Component({
  selector: 'app-cvm-notice',
  standalone: true,
  imports: [LegalDraftNoticeComponent, PageHeaderComponent, RouterLink],
  template: `
    <article class="max-w-reading mx-auto px-4 py-10">
      <app-page-header
        title="Aviso CVM"
        question="A fronteira entre analisar e recomendar, e de que lado o fiance está."
      />

      <div class="mt-8">
        <app-legal-draft-notice />
      </div>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">O que o fiance não faz</h2>
        <p class="fi-body text-ink m-0 mt-3">
          As Resoluções CVM 19 e 20 tratam de <strong>análise</strong> e de
          <strong>consultoria</strong> de valores mobiliários — atividades que exigem registro e que
          envolvem recomendação individualizada, feita para a situação de uma pessoa específica.
        </p>
        <p class="fi-body text-ink m-0 mt-3">
          O fiance não presta nenhuma das duas. Ele aplica critérios objetivos e públicos sobre
          dados públicos e mostra o resultado com a conta à vista. Ninguém aqui olha a sua situação
          e diz o que você deveria comprar.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">O quanto o produto afirma é configuração, não opinião</h2>
        <p class="fi-body text-ink m-0 mt-3">
          O nível de afirmação do fiance é um ajuste explícito do sistema, com três posturas. Ele
          não varia por tela nem por usuário:
        </p>

        <table class="data-table mt-4">
          <thead>
            <tr>
              <th scope="col">Nível</th>
              <th scope="col">O que o produto diz</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="fi-label">1 · Descritivo</td>
              <td>Descreve a sua carteira. Não avalia ativo nem sugere operação.</td>
            </tr>
            <tr>
              <td class="fi-label">2 · Analítico</td>
              <td>
                Avalia ativo por critério objetivo, com a metodologia à vista, e não diz quanto
                comprar de quê.
              </td>
            </tr>
            <tr>
              <td class="fi-label">3 · Prescritivo</td>
              <td>Acrescentaria valor por ativo — quanto aportar em qual papel.</td>
            </tr>
          </tbody>
        </table>

        @if (modo(); as m) {
          <div class="notice notice-brand mt-4">
            <div>
              <p class="fi-label m-0">
                Postura em vigor agora: nível {{ m.level }} — {{ nomeDoNivel(m.level) }}
              </p>
              <p class="fi-body m-0 mt-1">{{ m.disclaimer }}</p>
            </div>
          </div>
        }

        <p class="fi-body text-ink-2 m-0 mt-4">
          O nível 3 existe no código e <strong>está desligado</strong> até haver parecer jurídico
          que o autorize. Enquanto isso, o valor por ativo simplesmente não sai do servidor — não é
          escondido na tela, é ausente da resposta.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">O que continua sendo seu</h2>
        <p class="fi-body text-ink m-0 mt-3">
          A decisão de investir, e o risco dela.
          <strong>Não há garantia de retorno</strong>, e nada no fiance considera a sua situação
          financeira, seus objetivos ou a sua tolerância a risco de forma individualizada. Para
          recomendação personalizada, procure profissional habilitado e registrado na CVM.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Orientação sobre dívida é outra coisa</h2>
        <p class="fi-body text-ink m-0 mt-3">
          Quando o fiance compara o custo de uma dívida com o que a sua carteira rende, ele está
          fazendo aritmética de taxa de juros — dívida não é valor mobiliário, e essa comparação não
          é recomendação de investimento. Ainda assim, a decisão é sua.
        </p>
      </section>

      <p class="fi-body text-ink-2 m-0 mt-8">
        Veja também os <a routerLink="/termos" class="btn-link">Termos de Uso</a> e a
        <a routerLink="/privacidade" class="btn-link">Política de Privacidade</a>.
      </p>
    </article>
  `,
})
export class CvmNoticeComponent {
  private readonly http = inject(HttpClient);

  readonly modo = signal<AffirmationMode | null>(null);

  private readonly nomes: Record<number, string> = {
    1: 'descritivo',
    2: 'analítico',
    3: 'prescritivo',
  };

  constructor() {
    this.http
      .get<AffirmationMode>(`${environment.apiBaseUrl}/public/affirmation`)
      .subscribe({ next: m => this.modo.set(m), error: () => this.modo.set(null) });
  }

  nomeDoNivel(level: number): string {
    return this.nomes[level] ?? '—';
  }
}
