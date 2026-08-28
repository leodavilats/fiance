import { ApplicationConfig, mergeApplicationConfig } from '@angular/core';
import { provideServerRendering, withRoutes } from '@angular/ssr';
import { appConfig } from './app.config';
import { serverRoutes } from './app.routes.server';

/**
 * O servidor usa exatamente os mesmos providers do navegador, mais a
 * renderização. Divergir os dois é como se chega a HTML que hidrata diferente
 * do que foi servido — e o usuário vê a tela piscar.
 */
const serverConfig: ApplicationConfig = {
  providers: [provideServerRendering(withRoutes(serverRoutes))],
};

export const config = mergeApplicationConfig(appConfig, serverConfig);
