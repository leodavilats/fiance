import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { configurarTelemetria } from './app/core/telemetry';
import { environment } from './environments/environment';

configurarTelemetria(environment.sentryDsn, environment.production ? 'production' : 'development');

bootstrapApplication(AppComponent, appConfig).catch(err => console.error(err));
