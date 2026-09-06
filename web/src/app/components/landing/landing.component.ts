import { HttpClient } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../core';
import { environment } from '../../../environments/environment';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import { LogoComponent } from '../logo/logo.component';
import { WordmarkComponent } from '../logo/wordmark.component';

interface LinhaDoMes {
  descricao: string;
  valor: number;
  tipo: 'entrada' | 'saida';
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    LucideAngularModule,
    RouterLink,
    HelpTooltipComponent,
    LogoComponent,
    WordmarkComponent,
  ],
  template: `
    <div class="max-w-reading mx-auto px-4 py-12">
      <header class="flex items-center gap-3">
        <app-logo [size]="32" />
        <app-wordmark [height]="18" />
      </header>

      <h1 class="fi-title text-ink m-0 mt-10 max-w-[34ch]">
        Quanto você tem investido, você sabe. Quanto sobrou este mês, provavelmente não.
      </h1>

      <p class="fi-body text-ink-2 m-0 mt-4 max-w-[52ch]">
        E é a sobra que decide o próximo aporte. Hoje ela mora num app, e a carteira mora em outro —
        então a decisão acontece de cabeça, uma vez por mês, com o número errado.
      </p>

      <section class="fi-block mt-12">
        <p class="fi-eyebrow text-ink-3 m-0">Um mês de exemplo</p>
        <h2 class="fi-title text-ink m-0 mt-1">O que o fiance passa a saber</h2>

        <div class="overflow-x-auto mt-4">
          <table class="data-table">
            <caption class="sr-only">
              Entradas e saídas de um mês de exemplo, terminando na sobra
            </caption>
            <thead>
              <tr>
                <th scope="col">Movimento</th>
                <th scope="col" class="num">Valor</th>
              </tr>
            </thead>
            <tbody>
              @for (linha of mes; track linha.descricao) {
                <tr>
                  <td class="text-ink">{{ linha.descricao }}</td>
                  <td
                    class="num"
                    [class.text-up]="linha.tipo === 'entrada'"
                    [class.text-down]="linha.tipo === 'saida'"
                  >
                    {{ linha.tipo === 'entrada' ? '+' : '−' }}{{ reais(linha.valor) }}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        <dl class="flex flex-wrap gap-x-12 gap-y-5 m-0 mt-6 pt-4 border-t border-hairline">
          <div>
            <dt class="fi-eyebrow text-ink-3">Sobra do mês</dt>
            <dd class="fi-money-xl text-ink m-0 mt-1">{{ reais(sobra()) }}</dd>
          </div>
        </dl>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">
          E o que ele faz com ela
          <app-help-tooltip
            term="a ordem da decisão"
            text="Dívida cara vem antes de aporte porque é aritmética de taxa: enquanto o juro
                  da dívida for maior que o retorno esperado da carteira, quitar rende mais que
                  investir. Dívida não é valor mobiliário, então isso não é recomendação de
                  investimento."
          />
        </h2>

        <div class="notice notice-attention mt-4">
          <lucide-icon name="circle-alert" size="18" aria-hidden="true"></lucide-icon>
          <div>
            <p class="fi-label m-0">R$ 890,00 do seu cartão estão no rotativo, a 14,9% ao mês</p>
            <p class="fi-body m-0 mt-1">
              Sua carteira rendeu 0,9% ao mês nos últimos doze meses. Enquanto essa diferença
              existir, quitar vem antes de aportar.
            </p>
          </div>
        </div>

        <p class="fi-body text-ink m-0 mt-5 max-w-[52ch]">
          Sobram <strong>{{ reais(sobra() - 890) }}</strong> depois disso. A meta que você declarou
          pede FIIs, e é a classe mais atrás — <strong>4,1 pontos</strong> abaixo do alvo. Não é um
          palpite sobre o futuro: é a distância entre onde a carteira está e onde você disse que ela
          deveria estar.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">O que já existe, e o que está sendo construído</h2>
        <p class="fi-body text-ink m-0 mt-3 max-w-[52ch]">
          A metade de trás já funciona: preço justo por três métodos, score com a conta à vista,
          imposto apurado por mês e categoria, carteira reconstruída a partir do livro-razão. Tudo
          para ativos da B3 — ações, FIIs, BDRs, ETFs e renda fixa.
        </p>
        <p class="fi-body text-ink m-0 mt-3 max-w-[52ch]">
          A metade da frente — o mês corrente — é o que falta. Quando ela existir, a sobra deixa de
          ser um número que você descobre no extrato e passa a ser o começo da próxima decisão.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Quer saber quando abrir?</h2>

        @if (enviado()) {
          <div class="notice notice-brand mt-4">
            <lucide-icon name="check" size="18" aria-hidden="true"></lucide-icon>
            <p class="fi-body m-0">
              Anotado. Avisamos {{ email() }} quando a parte do mês estiver de pé.
            </p>
          </div>
        } @else {
          <form class="mt-4 flex flex-wrap items-end gap-3" (submit)="enviar($event)">
            <div class="grow min-w-[16rem]">
              <label class="field-label" for="email-interesse">Seu e-mail</label>
              <input
                id="email-interesse"
                class="input"
                type="email"
                name="email"
                autocomplete="email"
                required
                [value]="email()"
                (input)="email.set($any($event.target).value)"
                placeholder="voce@exemplo.com"
              />
            </div>
            <button type="submit" class="btn-primary" [disabled]="enviando()">
              <lucide-icon name="arrow-right" size="16" aria-hidden="true"></lucide-icon>
              {{ enviando() ? 'Enviando…' : 'Quero saber' }}
            </button>
          </form>

          @if (erro()) {
            <p class="fi-caption text-adverse m-0 mt-3" role="alert">{{ erro() }}</p>
          }

          <p class="fi-caption text-ink-3 m-0 mt-3 max-w-[52ch]">
            Só para avisar do lançamento. Não vira newsletter e não vai para lugar nenhum — veja a
            <a routerLink="/privacidade" class="btn-link">Política de Privacidade</a>.
          </p>
        }
      </section>

      <footer class="mt-12 pt-6 border-t border-hairline">
        <p class="fi-caption text-ink-3 m-0 max-w-[52ch]">
          O fiance é ferramenta de análise, não consultoria de investimentos. Não há garantia de
          retorno, e nada aqui considera a sua situação financeira de forma individualizada.
          <a routerLink="/aviso-cvm" class="btn-link">Aviso CVM</a> ·
          <a routerLink="/termos" class="btn-link">Termos</a> ·
          <a routerLink="/privacidade" class="btn-link">Privacidade</a>
        </p>
      </footer>
    </div>
  `,
})
export class LandingComponent {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly mes: LinhaDoMes[] = [
    { descricao: 'Salário, dia 5', valor: 6418.73, tipo: 'entrada' },
    { descricao: 'Aluguel', valor: 2150, tipo: 'saida' },
    { descricao: 'Mercado e dia a dia', valor: 1204.15, tipo: 'saida' },
    { descricao: 'Fatura do cartão', valor: 1099.92, tipo: 'saida' },
    { descricao: 'Energia', valor: 187.44, tipo: 'saida' },
    { descricao: 'Internet', valor: 129.9, tipo: 'saida' },
  ];

  readonly sobra = computed(() =>
    this.mes.reduce((total, l) => total + (l.tipo === 'entrada' ? l.valor : -l.valor), 0)
  );

  readonly email = signal('');
  readonly enviando = signal(false);
  readonly enviado = signal(false);
  readonly erro = signal('');

  constructor() {
    if (this.auth.isAuthenticated()) {
      void this.router.navigateByUrl('/hoje');
    }
  }

  reais(valor: number): string {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
    });
  }

  enviar(evento: Event): void {
    evento.preventDefault();
    if (this.enviando()) return;

    this.erro.set('');
    this.enviando.set(true);

    this.http
      .post<{ registered: boolean }>(`${environment.apiBaseUrl}/public/interest`, {
        email: this.email(),
        source: 'landing',
      })
      .subscribe({
        next: () => {
          this.enviando.set(false);
          this.enviado.set(true);
        },
        error: () => {
          this.enviando.set(false);
          this.erro.set('Não consegui registrar agora. Tente de novo em alguns instantes.');
        },
      });
  }
}
