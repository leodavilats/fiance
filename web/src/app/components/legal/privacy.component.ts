import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { LegalDraftNoticeComponent } from './legal-draft-notice.component';

@Component({
  selector: 'app-privacy',
  standalone: true,
  imports: [LegalDraftNoticeComponent, PageHeaderComponent, RouterLink],
  template: `
    <article class="max-w-reading mx-auto px-4 py-10">
      <app-page-header
        title="Política de Privacidade"
        question="Que dado o fiance guarda, com quem compartilha e como você o leva embora."
      />
      <p class="fi-caption text-ink-3 m-0 mb-8">Versão de 5 de setembro de 2026.</p>

      <div class="mt-8">
        <app-legal-draft-notice />
      </div>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">O resumo, antes do detalhe</h2>
        <p class="fi-body text-ink m-0 mt-3">
          Sua carteira não sai do produto. Nenhuma fonte externa recebe quanto você tem, quanto
          pagou ou quanto ganhou — a BRAPI recebe apenas o código do papel, o mesmo que qualquer
          pessoa digita numa busca. Você pode exportar tudo e apagar a conta quando quiser, sem
          precisar falar com ninguém e sem plano pago.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Que dado é coletado, e para quê</h2>

        <table class="data-table mt-4">
          <thead>
            <tr>
              <th scope="col">Dado</th>
              <th scope="col">Finalidade</th>
              <th scope="col">Base legal (LGPD)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Nome, e-mail e foto da conta Google</td>
              <td>Identificar você e manter a sessão</td>
              <td>Execução de contrato (art. 7º, V)</td>
            </tr>
            <tr>
              <td>Posições, renda fixa, lançamentos, metas e preferências</td>
              <td>Calcular a análise que você pediu</td>
              <td>Execução de contrato (art. 7º, V)</td>
            </tr>
            <tr>
              <td>Eventos de uso (vocabulário fechado, sem ticker e sem valor)</td>
              <td>Entender que telas funcionam e onde o produto trava</td>
              <td>Legítimo interesse (art. 7º, IX)</td>
            </tr>
            <tr>
              <td>Token de notificação do aparelho</td>
              <td>Enviar alerta que você configurou</td>
              <td>Consentimento (art. 7º, I)</td>
            </tr>
            <tr>
              <td>Log técnico com identificador de requisição e IP</td>
              <td>Segurança, limite de uso e diagnóstico de erro</td>
              <td>Legítimo interesse (art. 7º, IX)</td>
            </tr>
          </tbody>
        </table>

        <p class="fi-body text-ink-2 m-0 mt-4">
          O dicionário de eventos é fechado no servidor: um evento que carregue ticker ou valor é
          <strong>recusado</strong>, não filtrado depois. Isso é código, não promessa.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Com quem o dado é compartilhado</h2>
        <table class="data-table mt-4">
          <thead>
            <tr>
              <th scope="col">Terceiro</th>
              <th scope="col">O que recebe</th>
              <th scope="col">O que não recebe</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Google (entrar com Google)</td>
              <td>A própria autenticação; nome, e-mail e foto voltam de lá</td>
              <td>Nada da sua carteira</td>
            </tr>
            <tr>
              <td>BRAPI (cotação e fundamento)</td>
              <td>O código do papel consultado</td>
              <td>Quem consultou, quanto tem, quanto pagou</td>
            </tr>
            <tr>
              <td>Banco Central — SGS (CDI, Selic, IPCA)</td>
              <td>Nada seu: a consulta é de série pública</td>
              <td>Tudo</td>
            </tr>
            <tr>
              <td>Firebase (notificação)</td>
              <td>O token do aparelho e o texto do alerta</td>
              <td>Sua carteira</td>
            </tr>
            <tr>
              <td>Provedor de hospedagem e de banco</td>
              <td>Armazena o dado em nosso nome, como operador</td>
              <td>Não usa o dado para finalidade própria</td>
            </tr>
          </tbody>
        </table>
        <p class="fi-body text-ink-2 m-0 mt-4">
          Quando a cobrança for ligada, o provedor de pagamento receberá identidade e dado de
          cobrança — nunca dado de carteira. Esta seção será atualizada nomeando o provedor
          <em>antes</em> de qualquer cobrança existir.
        </p>
        <p class="fi-body text-ink m-0 mt-3">
          <strong>Não vendemos dado pessoal</strong> e não o usamos para publicidade.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Por quanto tempo o dado fica</h2>
        <ul class="fi-body text-ink mt-3 pl-5 list-disc">
          <li>
            <strong>Enquanto a conta existir</strong>: carteira, lançamentos, metas e preferências.
          </li>
          <li>
            <strong>Ao apagar a conta</strong>: tudo isso é removido de imediato. Fica apenas um
            registro anonimizado de que aquela conta existiu e foi apagada — sem nome, sem e-mail e
            sem foto —, para que o mesmo identificador não seja reaproveitado.
          </li>
          <li>
            <strong>Log técnico</strong>: mantido pelo prazo necessário à segurança e diagnóstico.
          </li>
        </ul>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Seus direitos, e como exercê-los</h2>
        <p class="fi-body text-ink m-0 mt-3">
          A LGPD garante confirmação, acesso, correção, portabilidade, eliminação e revogação de
          consentimento. Dois deles já estão implementados como botão, sem intermediário:
        </p>
        <ul class="fi-body text-ink mt-3 pl-5 list-disc">
          <li>
            <strong>Exportar tudo</strong> — Você → Conta devolve um arquivo com todo o dado
            vinculado a você.
          </li>
          <li>
            <strong>Apagar a conta</strong> — Você → Conta remove o dado, sem passar por atendimento
            e sem cerca de plano.
          </li>
        </ul>
        <p class="fi-body text-ink m-0 mt-3">
          Para os demais direitos, ou para falar com o encarregado pelo tratamento de dados, escreva
          para o endereço indicado em Você → Conta. Respondemos no prazo da LGPD.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Segurança</h2>
        <p class="fi-body text-ink m-0 mt-3">
          O acesso é isolado por conta na camada de dados: uma consulta sem dono não devolve
          carteira de ninguém. A sessão tem prazo curto e a renovação é de uso único — reaproveitar
          uma renovação derruba a sessão em todos os aparelhos. Segredos e dado sensível são
          removidos do log antes de ele ser gravado.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">Mudanças nesta política</h2>
        <p class="fi-body text-ink m-0 mt-3">
          Quando ela mudar de forma relevante, a data no topo muda e avisamos dentro do produto
          antes da mudança valer. Veja também os
          <a routerLink="/termos" class="btn-link">Termos de Uso</a> e o
          <a routerLink="/aviso-cvm" class="btn-link">Aviso CVM</a>.
        </p>
      </section>
    </article>
  `,
})
export class PrivacyComponent {}
