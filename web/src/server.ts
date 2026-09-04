import {
  AngularNodeAppEngine,
  createNodeRequestHandler,
  isMainModule,
  writeResponseToNodeResponse,
} from '@angular/ssr/node';
import express from 'express';
import { join } from 'node:path';
import { environment } from './environments/environment';

const browserDistFolder = join(import.meta.dirname, '../browser');

const app = express();

const allowedHosts = (process.env['ALLOWED_HOSTS'] ?? 'localhost,127.0.0.1')
  .split(',')
  .map(host => host.trim())
  .filter(Boolean);

const angularApp = new AngularNodeAppEngine({ allowedHosts });

const SITE_URL = (() => {
  const declarado = process.env['SITE_URL']?.trim();
  if (declarado) return declarado.replace(/\/$/, '');

  if (process.env['NODE_ENV'] === 'production') {
    throw new Error(
      'SITE_URL não definido. Sitemap e canônicas apontariam para o domínio errado ' +
        'sem nada falhar — e é por elas que a única página pública é indexada.'
    );
  }

  return 'http://localhost:4000';
})();

const SITEMAP_TTL_MS = 6 * 60 * 60 * 1000;
let sitemapCache: { xml: string; builtAt: number } | null = null;

const SITEMAP_FETCH_TIMEOUT_MS = 8_000;

async function buildSitemap(): Promise<string> {
  const response = await fetch(`${environment.apiBaseUrl}/public/universe`, {
    signal: AbortSignal.timeout(SITEMAP_FETCH_TIMEOUT_MS),
  });
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
    res.status(503).type('text/plain').send('sitemap indisponível');
  }
});

app.get('/robots.txt', (_req, res) => {
  res
    .type('text/plain')
    .send(
      [
        'User-agent: *',
        'Allow: /$',
        'Allow: /ativo/',
        'Disallow: /',
        '',
        `Sitemap: ${SITE_URL}/sitemap.xml`,
        '',
      ].join('\n')
    );
});

const CSP = [
  "default-src 'self'",
  "script-src 'self' https://accounts.google.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  "img-src 'self' data: https:",
  `connect-src 'self' ${new URL(environment.apiBaseUrl).origin} https://accounts.google.com`,
  'frame-src https://accounts.google.com',
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join('; ');

app.use((_req, res, next) => {
  res.setHeader('Content-Security-Policy', CSP);
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  if (process.env['NODE_ENV'] === 'production') {
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  }
  next();
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
