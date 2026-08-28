import {
  AngularNodeAppEngine,
  createNodeRequestHandler,
  isMainModule,
  writeResponseToNodeResponse,
} from '@angular/ssr/node';
import express from 'express';
import { join } from 'node:path';
import { environment } from './environments/environment';

/**
 * Servidor de renderização.
 *
 * Existe por um motivo comercial, não técnico: o modelo de receita não comporta
 * mídia paga — o teto de CAC é uma fração do custo de instalação qualificada em
 * finanças no Brasil —, então o único canal que escala sem verba é a página de
 * ativo indexável. Página renderizada no cliente é invisível para busca.
 */

const browserDistFolder = join(import.meta.dirname, '../browser');

const app = express();

/**
 * Hosts autorizados a receber renderização.
 *
 * O Angular recusa `Host` desconhecido para não virar um proxy de SSRF, e o
 * domínio é fato de deploy — não de build. Por isso vem do ambiente e não do
 * `angular.json`: mudar de domínio não deveria exigir recompilar o bundle.
 */
const allowedHosts = (process.env['ALLOWED_HOSTS'] ?? 'localhost,127.0.0.1')
  .split(',')
  .map(host => host.trim())
  .filter(Boolean);

const angularApp = new AngularNodeAppEngine({ allowedHosts });

/** Base pública do site, para as URLs absolutas do sitemap. */
const SITE_URL = (process.env['SITE_URL'] ?? 'https://fiance.app').replace(/\/$/, '');

/** O sitemap muda no máximo uma vez por dia; buscar o universo a cada hit é desperdício. */
const SITEMAP_TTL_MS = 6 * 60 * 60 * 1000;
let sitemapCache: { xml: string; builtAt: number } | null = null;

async function buildSitemap(): Promise<string> {
  const response = await fetch(`${environment.apiBaseUrl}/public/universe`);
  if (!response.ok) throw new Error(`universo indisponível: ${response.status}`);

  const { tickers, lastmod } = (await response.json()) as {
    tickers: string[];
    lastmod: string;
  };

  const urls = tickers
    .map(
      ticker =>
        `  <url>\n` +
        `    <loc>${SITE_URL}/ativo/${encodeURIComponent(ticker)}</loc>\n` +
        `    <lastmod>${lastmod}</lastmod>\n` +
        `    <changefreq>daily</changefreq>\n` +
        `  </url>`
    )
    .join('\n');

  return (
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    `${urls}\n` +
    `</urlset>\n`
  );
}

app.get('/sitemap.xml', async (_req, res) => {
  try {
    if (!sitemapCache || Date.now() - sitemapCache.builtAt > SITEMAP_TTL_MS) {
      sitemapCache = { xml: await buildSitemap(), builtAt: Date.now() };
    }
    res.type('application/xml').send(sitemapCache.xml);
  } catch {
    // Servir um sitemap vazio é pior que não servir: o robô o trata como
    // "o site encolheu" e desindexa. 503 faz ele voltar depois.
    res.status(503).type('text/plain').send('sitemap indisponível');
  }
});

app.get('/robots.txt', (_req, res) => {
  // Só a página de ativo é pública. As telas de sessão não têm o que indexar e
  // apontar o robô para elas gasta orçamento de rastreio em redirect de login.
  res
    .type('text/plain')
    .send(
      [
        'User-agent: *',
        'Allow: /ativo/',
        'Disallow: /hoje',
        'Disallow: /carteira',
        'Disallow: /descobrir',
        'Disallow: /estrategia',
        'Disallow: /voce',
        'Disallow: /login',
        '',
        `Sitemap: ${SITE_URL}/sitemap.xml`,
        '',
      ].join('\n')
    );
});

app.use(
  express.static(browserDistFolder, {
    maxAge: '1y',
    index: false,
    redirect: false,
  })
);

app.use((req, res, next) => {
  angularApp
    .handle(req)
    .then(response => (response ? writeResponseToNodeResponse(response, res) : next()))
    .catch(next);
});

if (isMainModule(import.meta.url)) {
  const port = process.env['PORT'] || 4000;
  app.listen(port, () => {
    console.log(`fiance: renderização no servidor em http://localhost:${port}`);
  });
}

export const reqHandler = createNodeRequestHandler(app);
