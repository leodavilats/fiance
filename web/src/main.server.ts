import { BootstrapContext, bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { config } from './app/app.config.server';

/**
 * Bootstrap do servidor. O `AngularNodeAppEngine` chama isto por requisição e
 * passa o `context` — sem ele o Angular 22 não sabe em qual plataforma está e
 * falha com NG0401.
 */
export default (context: BootstrapContext) => bootstrapApplication(AppComponent, config, context);
