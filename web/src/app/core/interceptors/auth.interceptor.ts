import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, from, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/** Rotas que não levam token e não devem tentar renovar sessão. */
const ANONYMOUS = ['/auth/google', '/auth/refresh'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);

  if (ANONYMOUS.some(path => req.url.includes(path))) {
    return next(req);
  }

  const token = auth.token();
  if (!token) {
    return next(req);
  }

  const withToken = (value: string) =>
    req.clone({ setHeaders: { Authorization: `Bearer ${value}` } });

  return next(withToken(token)).pipe(
    catchError((error: unknown) => {
      // O acesso vale uma hora. Um 401 aqui quase sempre é token vencido, não
      // sessão encerrada — renovar uma vez e repetir evita jogar o usuário no
      // login no meio de uma navegação.
      if (!(error instanceof HttpErrorResponse) || error.status !== 401) {
        return throwError(() => error);
      }

      return from(auth.refreshSession()).pipe(
        switchMap(renewed => {
          const renewedToken = renewed ? auth.token() : null;
          if (!renewedToken) {
            return throwError(() => error);
          }
          return next(withToken(renewedToken));
        })
      );
    })
  );
};
