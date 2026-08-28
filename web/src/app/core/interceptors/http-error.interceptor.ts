import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, finalize, retry, throwError, timeout, TimeoutError } from 'rxjs';
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
      let errorMessage = 'Erro ao processar requisição';

      if (error instanceof TimeoutError) {
        errorMessage = 'A operação demorou demais. Tente novamente.';
      } else if (error instanceof HttpErrorResponse) {
        switch (error.status) {
          case 0:
            errorMessage = 'Sem conexão com o servidor. Verifique se o backend está rodando.';
            break;
          case 401:
            // Chegar aqui significa que a renovação já foi tentada e falhou.
            // `clearSession` e não `logout`: não há por que postar um logout
            // com um token que o servidor acabou de recusar.
            errorMessage = 'Sessão expirada. Faça login novamente.';
            auth.clearSession();
            router.navigateByUrl('/login');
            break;
          case 429:
            errorMessage =
              error.error?.detail || 'Muitas requisições em pouco tempo. Aguarde um minuto.';
            break;
          case 404:
            errorMessage = error.error?.detail || 'Recurso não encontrado.';
            break;
          case 422:
            errorMessage = 'Dados inválidos. Verifique os campos e tente novamente.';
            break;
          case 500:
            errorMessage = error.error?.detail || 'Erro interno do servidor.';
            break;
          case 503:
            errorMessage = 'Serviço temporariamente indisponível. Aguarde e tente novamente.';
            break;
          default:
            errorMessage = error.error?.detail || error.message || `Erro ${error.status}`;
        }
      }

      snackbar.showError(errorMessage);
      return throwError(() => error);
    }),
    finalize(() => {
      loading.hide();
    })
  );
};
