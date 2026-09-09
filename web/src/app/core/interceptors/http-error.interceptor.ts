import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import { inject, PLATFORM_ID } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, finalize, retry, throwError, timeout, TimeoutError } from 'rxjs';
import { detalheUtil, mensagemDeErro } from '../error-message';
import { AuthService } from '../services/auth.service';
import { LoadingService } from '../services/loading.service';
import { SnackbarService } from '../services/snackbar.service';

const RETRYABLE_METHODS = ['GET'];
const MAX_RETRIES = 1;

const LONG_TIMEOUT_PATTERNS = [
  '/dip-scanner',
  '/opportunities',
  '/dashboard',
  '/strategy',
  '/sectors-summary',
  '/quick-invest',
];

const LONG_TIMEOUT_MS = 45_000;
const DEFAULT_TIMEOUT_MS = 20_000;

export const httpErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const noNavegador = isPlatformBrowser(inject(PLATFORM_ID));
  const loading = inject(LoadingService);
  const snackbar = inject(SnackbarService);
  const auth = inject(AuthService);
  const router = inject(Router);

  const isLongRequest = LONG_TIMEOUT_PATTERNS.some(p => req.url.includes(p));
  const requestTimeout = isLongRequest ? LONG_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;
  const canRetry = RETRYABLE_METHODS.includes(req.method) && !isLongRequest;

  loading.show();

  let pipeline = next(req).pipe(timeout(requestTimeout));

  if (canRetry) {
    pipeline = pipeline.pipe(retry({ count: MAX_RETRIES, delay: 1000 }));
  }

  return pipeline.pipe(
    catchError((error: HttpErrorResponse | TimeoutError) => {
      if (error instanceof HttpErrorResponse && error.status === 402) {
        return throwError(() => error);
      }

      /*
       * A frase é a de `mensagemDeErro`, a mesma que a tela mostra em `<app-async-state>`.
       * Aqui só se decide o efeito colateral do 401 e se há detalhe de domínio a acrescentar —
       * `Erro 500` e "verifique se o backend está rodando" eram texto de quem desenvolve.
       */
      let errorMessage = mensagemDeErro(error, 'concluir esta ação');

      if (error instanceof HttpErrorResponse && error.status === 401) {
        const tinhaSessao = !!(auth.token() || auth.refreshToken());
        if (noNavegador && tinhaSessao) {
          auth.clearSession();
          router.navigateByUrl('/login');
        } else {
          errorMessage = '';
        }
      } else {
        errorMessage = detalheUtil(error) ?? errorMessage;
      }

      snackbar.showError(errorMessage);
      return throwError(() => error);
    }),
    finalize(() => {
      loading.hide();
    })
  );
};
