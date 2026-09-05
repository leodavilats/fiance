const CABECALHOS_PERMITIDOS = new Set(['x-request-id', 'content-type']);

const SEGMENTO_IDENTIFICADOR = /^(?:[A-Z][A-Z0-9]{3}\d{1,2}|\d+|[0-9a-fA-F-]{16,})$/;

const SIGILO_NA_URL =
  /\b(token|api_key|apikey|access_token|refresh_token|secret|password|senha)=([^&\s"'>]+)/gi;

const DINHEIRO = /R\$\s?-?[\d.,]+/g;

const NUMERO_ENTRE_PARENTESES = /\((-?\d[\d.,]*)\)/g;

export function limparCaminho(url: string): string {
  let prefixo = '';
  let caminho = url;

  const separador = url.indexOf('://');
  if (separador >= 0) {
    const resto = url.slice(separador + 3);
    const barra = resto.indexOf('/');
    if (barra < 0) return url;
    prefixo = url.slice(0, separador + 3) + resto.slice(0, barra);
    caminho = resto.slice(barra);
  }

  const semQuery = caminho.split('?')[0].split('#')[0];
  const limpo = semQuery
    .split('/')
    .map(parte => (SEGMENTO_IDENTIFICADOR.test(parte) ? '{id}' : parte))
    .join('/');

  return prefixo + limpo;
}

export function limparTexto(texto: string): string {
  return texto
    .replace(SIGILO_NA_URL, '$1=[redigido]')
    .replace(DINHEIRO, 'R$ [redigido]')
    .replace(NUMERO_ENTRE_PARENTESES, '([redigido])');
}

interface EventoSentry {
  message?: string;
  request?: Record<string, unknown>;
  user?: Record<string, unknown>;
  extra?: unknown;
  contexts?: Record<string, unknown>;
  breadcrumbs?: { message?: string; data?: unknown }[];
  exception?: { values?: { value?: string }[] };
}

export function limparEvento(evento: EventoSentry): EventoSentry {
  if (evento.request) {
    const { method, url, headers } = evento.request as {
      method?: string;
      url?: string;
      headers?: Record<string, string>;
    };

    const limpo: Record<string, unknown> = {};
    if (method) limpo['method'] = method;
    if (url) limpo['url'] = limparCaminho(url);
    if (headers) {
      limpo['headers'] = Object.fromEntries(
        Object.entries(headers).filter(([nome]) => CABECALHOS_PERMITIDOS.has(nome.toLowerCase()))
      );
    }
    evento.request = limpo;
  }

  if (evento.user) {
    const id = evento.user['id'];
    evento.user = id ? { id } : {};
  }

  delete evento.extra;

  for (const trilha of evento.breadcrumbs ?? []) {
    delete trilha.data;
    if (typeof trilha.message === 'string') trilha.message = limparTexto(trilha.message);
  }

  if (typeof evento.message === 'string') evento.message = limparTexto(evento.message);

  for (const excecao of evento.exception?.values ?? []) {
    if (typeof excecao.value === 'string') excecao.value = limparTexto(excecao.value);
  }

  return evento;
}

export async function configurarTelemetria(dsn: string, ambiente: string): Promise<boolean> {
  if (!dsn.trim()) return false;

  try {
    const Sentry = await import('@sentry/angular');
    Sentry.init({
      dsn,
      environment: ambiente,
      sendDefaultPii: false,
      beforeSend: limparEvento as never,
      beforeBreadcrumb: trilha => {
        delete trilha.data;
        if (typeof trilha.message === 'string') trilha.message = limparTexto(trilha.message);
        return trilha;
      },
    });
    return true;
  } catch (erro) {
    console.error('Telemetria não pôde ser ligada; o app segue sem ela.', erro);
    return false;
  }
}
