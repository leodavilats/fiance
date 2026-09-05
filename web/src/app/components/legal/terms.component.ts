import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { LegalDraftNoticeComponent } from './legal-draft-notice.component';

@Component({
  selector: 'app-terms',
  standalone: true,
  imports: [LegalDraftNoticeComponent, PageHeaderComponent, RouterLink],
  template: `
    <article class="max-w-reading mx-auto px-4 py-10">
      <app-page-header
        title="Termos de Uso"
        question="O que o fiance é, o que ele não é, e o que fica sendo seu."
      />
      <p class="fi-caption text-ink-3 m-0 mb-8">Versão de 5 de setembro de 2026.</p>

      <div class="mt-8">
        <app-legal-draft-notice />
      </div>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">1. O que o fiance é</h2>
        <p class="fi-body text-ink m-0 mt-3">
          O fiance é uma <strong>ferramenta de análise de investimentos</strong>. Ele lê dados
          públicos de mercado, aplica critérios objetivos e mostra o resultado com a metodologia à
          vista: de onde veio cada número, que premissa ele assume e o que o derrubaria.
        </p>
        <p class="fi-body text-ink m-0 mt-3">
          O fiance <strong>não é</strong> consultoria de valores mobiliários, não é análise de
          valores mobiliários prestada por analista credenciado, não é corretora, não é
          administrador de carteira e não custodia dinheiro nem ativo de ninguém. Nada aqui é
          recomendação personalizada de compra ou venda. O que está publicado sobre essa fronteira
          está em <a routerLink="/aviso-cvm" class="btn-link">Aviso CVM</a>.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">2. Não há promessa de resultado</h2>
        <p class="fi-body text-ink m-0 mt-3">
          <strong>Não há garantia de retorno.</strong> Toda projeção que o fiance mostra é uma faixa
          de cenários, não uma previsão, e rentabilidade passada não indica rentabilidade futura. As
          decisões de investimento são suas, e o risco delas é seu.
        </p>
        <p class="fi-body text-ink m-0 mt-3">
          Os cálculos podem conter erro. Quando encontramos um, ou consertamos ou escondemos o
          número com um aviso — não deixamos número errado com cara de número certo.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">3. O dado que você lança é seu</h2>
        <p class="fi-body text-ink m-0 mt-3">
          Você é responsável pelo que lança: posições, preços, datas, extratos importados. O fiance
          calcula sobre o que recebe — carteira incompleta ou preço médio errado produz análise
          errada, e ele não tem como saber disso sozinho.
        </p>
        <p class="fi-body text-ink m-0 mt-3">
          A qualquer momento você pode <strong>exportar tudo</strong> ou
          <strong>apagar a conta inteira</strong>, em Você → Conta. Nenhuma das duas coisas fica
          atrás de plano pago, e a exclusão remove o dado de fato — não o marca como oculto.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">4. Apuração de imposto</h2>
        <p class="fi-body text-ink m-0 mt-3">
          O fiance apura ganho de capital em renda variável por mês e por categoria, a partir do que
          você lançou no livro-razão, e mostra o cálculo. É uma
          <strong>estimativa de apoio</strong>: ela não substitui a apuração oficial, não emite
          DARF, não cobre day trade e não considera a sua situação fiscal completa. Confira com seu
          contador antes de declarar.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">5. Fontes de dado de mercado</h2>
        <p class="fi-body text-ink m-0 mt-3">
          Cotação, indicador fundamentalista e provento vêm da BRAPI; CDI, Selic e IPCA vêm do Banco
          Central (SGS). O fiance não controla essas fontes. Quando uma delas cai ou devolve número
          implausível, o produto avisa a origem do dado que está mostrando — inclusive quando é
          cache vencido ou estimativa.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">6. Uso aceitável</h2>
        <p class="fi-body text-ink m-0 mt-3">
          A conta é pessoal e intransferível. Não é permitido raspar o serviço em escala, revender o
          acesso, contornar limites de uso, nem apresentar a análise do fiance como recomendação
          profissional sua a terceiros.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">7. Disponibilidade e mudanças</h2>
        <p class="fi-body text-ink m-0 mt-3">
          O serviço é oferecido no estado em que se encontra, sem garantia de disponibilidade
          contínua. Podemos mudar, suspender ou encerrar funcionalidades. Quando a mudança afetar o
          que você já lançou, avisamos antes e mantemos a exportação funcionando.
        </p>
      </section>

      <section class="fi-block">
        <h2 class="fi-title text-ink m-0">8. Lei aplicável e contato</h2>
        <p class="fi-body text-ink m-0 mt-3">
          Estes termos são regidos pela lei brasileira. Dúvidas, pedidos de exclusão e exercício de
          direitos previstos na LGPD: veja o canal indicado na
          <a routerLink="/privacidade" class="btn-link">Política de Privacidade</a>.
        </p>
      </section>
    </article>
  `,
})
export class TermsComponent {}
