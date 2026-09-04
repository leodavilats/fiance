import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { FollowedSuggestionsComponent } from '../market/followed-suggestions/followed-suggestions.component';
import { ActivityFeedComponent } from './activity-feed.component';

/**
 * `/hoje/atividade` — a mesma leitura do drawer, endereçável.
 *
 * A arquitetura de informação declara Atividade como sub-rota de Hoje; o drawer
 * é conveniência, não substituto. Link salvo continua sendo contrato.
 */
@Component({
  selector: 'app-atividade-page',
  standalone: true,
  imports: [ActivityFeedComponent, FollowedSuggestionsComponent, LucideAngularModule, RouterLink],
  template: `
    <div class="max-w-reading">
      <a
        routerLink="/hoje"
        class="fi-caption text-ink-2 no-underline inline-flex items-center gap-1"
      >
        <lucide-icon name="arrow-left" size="12" aria-hidden="true"></lucide-icon>
        Hoje
      </a>

      <h1 class="fi-title text-ink m-0 mt-3">O que aconteceu</h1>
      <p class="fi-body text-ink-2 m-0 mt-1 mb-6">
        Mudanças de veredito, desvios de meta, vencimentos e proventos lançados — em ordem, do mais
        recente para o mais antigo.
      </p>

      <app-activity-feed />

      <!--
        "Sugestões que você seguiu" vivia no fim de Estratégia, depois do plano
        e sem título de seção na estrutura da página. É histórico do que já
        aconteceu, e o lugar do histórico é aqui.
      -->
      <div class="mt-8 pt-6 border-t border-hairline">
        <app-followed-suggestions />
      </div>
    </div>
  `,
})
export class AtividadePageComponent {}
