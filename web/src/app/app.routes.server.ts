import { RenderMode, ServerRoute } from '@angular/ssr';

/**
 * Quem renderiza o quê.
 *
 * A regra é uma só e vem do negócio, não da técnica: **renderiza no servidor o
 * que precisa ser indexado; o resto continua no cliente.** O produto vive de
 * aquisição orgânica — o modelo não comporta CAC pago —, e a única página que
 * um robô de busca tem motivo para ler é a do ativo.
 *
 * Tudo que depende de sessão fica em `Client` de propósito. Renderizar no
 * servidor uma tela de carteira significaria buscar dado de titular durante o
 * SSR, e é assim que se serve a carteira de uma pessoa para outra: basta um
 * cache na frente. A fronteira é literal, não uma convenção.
 */
export const serverRoutes: ServerRoute[] = [
  {
    // A página que é o canal de aquisição. Server e não Prerender porque o
    // universo tem centenas de tickers e o conteúdo muda todo pregão — gerar
    // tudo no build entregaria preço de ontem.
    path: 'ativo/:ticker',
    renderMode: RenderMode.Server,
  },
  {
    path: '**',
    renderMode: RenderMode.Client,
  },
];
