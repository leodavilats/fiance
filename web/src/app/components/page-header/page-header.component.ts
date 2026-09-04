import { Component, input } from '@angular/core';

/**
 * O nome da tela, a pergunta que ela responde e o recorte ativo.
 *
 * Existe porque 15 das 21 rotas não tinham `<h1>` nenhum, e as duas mais
 * importantes — Hoje e Carteira — só tinham um dentro do ramo de carteira
 * vazia: na operação normal os dois destinos principais abriam sem cabeçalho
 * de nível 1. "Onde estou?" só tinha resposta na navegação, no topo da página.
 *
 * O papel tipográfico é `fi-title`, não um papel novo. As duas rotas que já
 * acertavam (`/descobrir/oportunidades` e `/carteira/composicao`) usavam
 * exatamente isso, e inventar um `fi-page` em `tokens.json` criaria vocabulário
 * gerado sem consumidor no Flutter — a armadilha já catalogada no CLAUDE.md.
 *
 * `question` é a pergunta que a tela responde, escrita do lado de quem lê.
 * `scope` é o recorte ativo em texto — o filtro legível sem abrir os campos.
 */
@Component({
  selector: 'app-page-header',
  standalone: true,
  template: `
    <!--
      Um div, não um elemento header: o app já tem um header de banner, e um
      segundo com o mesmo nome dentro do main só cria ambiguidade de marco de
      página — inclusive para o teste de rota, que procurava por "header" e
      passou a encontrar dois. Quem dá o papel aqui é o h1.
    -->
    <div class="mb-5">
      <h1 class="fi-title text-ink m-0" tabindex="-1">{{ title() }}</h1>

      @if (question()) {
        <p class="fi-body text-ink-2 m-0 mt-1 max-w-reading">{{ question() }}</p>
      }

      @if (scope()) {
        <p class="fi-caption text-ink-3 m-0 mt-1">{{ scope() }}</p>
      }

      <ng-content />
    </div>
  `,
})
export class PageHeaderComponent {
  readonly title = input.required<string>();
  /** A pergunta que esta tela responde. Vazio quando a tela é configuração. */
  readonly question = input<string>('');
  /** O recorte ativo, já formatado por quem chama. */
  readonly scope = input<string>('');
}
