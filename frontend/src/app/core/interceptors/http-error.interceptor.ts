import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, finalize, retry, throwError, timeout, TimeoutError } from 'rxjs';
import { LoadingService } from '../services/loading.service';
import { SnackbarService } from '../services/snackbar.service';

const RETRYABLE_METHODS = ['GET'];
const MAX_RETRIES = 1;
// Rotas de scanner demoram mais — não usar timeout curto
const LONG_TIMEOUT_PATTERNS = ['/dip-scanner', '/opportunities', '/dashboard', '/strategy'];

export const httpErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const loading = inject(LoadingService);
  const snackbar = inject(SnackbarService);

  const isLongRequest = LONG_TIMEOUT_PATTERNS.some(p => req.url.includes(p));
  const requestTimeout = isLongRequest ? 300_000 : 90_000; // 5min ou 90s
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
