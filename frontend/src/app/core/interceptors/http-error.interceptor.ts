import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, finalize, throwError, timeout, TimeoutError } from 'rxjs';
import { LoadingService } from '../services/loading.service';
import { SnackbarService } from '../services/snackbar.service';

export const httpErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const loading = inject(LoadingService);
  const snackbar = inject(SnackbarService);

  loading.show();

  return next(req).pipe(
    timeout(60000),
    catchError((error: HttpErrorResponse | TimeoutError) => {
      let errorMessage = 'Erro ao processar requisição';
      
      if (error instanceof TimeoutError) {
        errorMessage = 'Tempo de resposta excedido. Tente novamente.';
      } else if (error instanceof HttpErrorResponse) {
        if (error.status === 0) {
          errorMessage = 'Não foi possível conectar ao servidor. Verifique sua conexão.';
        } else if (error.status === 404) {
          errorMessage = 'Recurso não encontrado.';
        } else if (error.status === 500) {
          errorMessage = 'Erro interno do servidor.';
        } else if (error.error?.detail) {
          errorMessage = error.error.detail;
        } else if (error.message) {
          errorMessage = error.message;
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
