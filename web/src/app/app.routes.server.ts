import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  {
    path: '',
    renderMode: RenderMode.Server,
  },
  {
    path: 'ativo/:ticker',
    renderMode: RenderMode.Server,
  },
  {
    path: 'termos',
    renderMode: RenderMode.Server,
  },
  {
    path: 'privacidade',
    renderMode: RenderMode.Server,
  },
  {
    path: 'aviso-cvm',
    renderMode: RenderMode.Server,
  },
  {
    path: '**',
    renderMode: RenderMode.Client,
  },
];
