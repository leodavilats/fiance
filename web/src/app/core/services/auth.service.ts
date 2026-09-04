import { HttpClient } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
          prompt: () => void;
          disableAutoSelect: () => void;
        };
      };
    };
  }
}

export interface AppUser {
  id: string;
  email: string;
  name: string;
  picture: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface LoginResponse extends TokenResponse {
  user: AppUser;
}

const TOKEN_KEY = 'fiance_access_token';
const REFRESH_KEY = 'fiance_refresh_token';
const REFERRAL_KEY = 'fiance_referral';
const USER_KEY = 'fiance_user';

const SCOPED_KEY_PREFIXES = ['portfolio_renda_fixa'];

/** Nome do cadeado que serializa a renovação entre abas do mesmo navegador. */
const REFRESH_LOCK = 'fiance_refresh';

interface JwtPayload {
  sub?: string;
  exp?: number;
}

function decodeJwt(token: string): JwtPayload | null {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(payload)) as JwtPayload;
  } catch {
    return null;
  }
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

  /**
   * No servidor não há sessão: a renderização é sempre anônima, de propósito.
   * A página de ativo tem que sair igual para o robô e para quem chega pelo
   * link — e ler token durante o SSR seria o caminho para servir a carteira de
   * uma pessoa a outra assim que houvesse cache na frente.
   */
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  private readonly _user = signal<AppUser | null>(this._loadUser());
  readonly user = this._user.asReadonly();

  private _gisInitialized = false;
  private _refreshInFlight: Promise<boolean> | null = null;

  /**
   * O acesso expira em uma hora; o refresh, em trinta dias. Ter só o acesso
   * vencido não é estar deslogado — é ter que renovar, e o guard de rota não
   * pode confundir as duas coisas.
   */
  isAuthenticated(): boolean {
    if (this.refreshToken()) return true;

    const token = this.token();
    if (!token) return false;

    const payload = decodeJwt(token);
    if (!payload?.exp) return true;

    return payload.exp * 1000 > Date.now();
  }

  token(): string | null {
    return this.isBrowser ? localStorage.getItem(TOKEN_KEY) : null;
  }

  refreshToken(): string | null {
    return this.isBrowser ? localStorage.getItem(REFRESH_KEY) : null;
  }

  /**
   * Troca o refresh por um par novo. O servidor rotaciona e queima o refresh
   * usado, então a chamada tem que ser compartilhada: duas requisições que
   * levam 401 ao mesmo tempo não podem disparar dois refreshes — o segundo
   * apresentaria um token já queimado e derrubaria a sessão.
   *
   * `_refreshInFlight` resolve isso dentro de uma aba, e só dentro dela: duas
   * abas têm dois serviços, dois nulos e o mesmo refresh no localStorage.
   * Abrir o app em duas abas e deixar o access token de 1h expirar derrubava a
   * sessão. O cadeado do navegador (Web Locks) serializa as abas, e quem entra
   * depois encontra o token já rotacionado e aproveita — em vez de apresentar
   * um queimado.
   */
  refreshSession(): Promise<boolean> {
    if (this._refreshInFlight) return this._refreshInFlight;

    const refresh = this.refreshToken();
    if (!refresh) return Promise.resolve(false);

    this._refreshInFlight = this._comCadeado(() => this._rotacionar(refresh)).finally(() => {
      this._refreshInFlight = null;
    });

    return this._refreshInFlight;
  }

  private _rotacionar(refreshAoEntrar: string): Promise<boolean> {
    const atual = this.refreshToken();
    if (!atual) return Promise.resolve(false);

    // Outra aba renovou enquanto esperávamos o cadeado. O refresh que
    // tínhamos já foi queimado por ela; o que está guardado agora é válido, e
    // apresentar o antigo é exatamente o que derrubava a sessão.
    if (atual !== refreshAoEntrar) return Promise.resolve(true);

    return firstValueFrom(
      this.http.post<TokenResponse>(`${this.base}/auth/refresh`, { refresh_token: atual })
    )
      .then(res => {
        this._storeTokens(res);
        return true;
      })
      .catch(() => false);
  }

  private _comCadeado(fn: () => Promise<boolean>): Promise<boolean> {
    const locks = this.isBrowser
      ? (navigator as Navigator & { locks?: LockManager }).locks
      : undefined;

    if (!locks) return fn();

    return locks.request(REFRESH_LOCK, fn);
  }

  private _storeTokens(res: TokenResponse): void {
    if (!this.isBrowser) return;
    localStorage.setItem(TOKEN_KEY, res.access_token);
    localStorage.setItem(REFRESH_KEY, res.refresh_token);
  }

  userId(): string | null {
    const fromUser = this._user()?.id;
    if (fromUser) return fromUser;

    const token = this.token();
    return token ? (decodeJwt(token)?.sub ?? null) : null;
  }

  scopedKey(base: string): string {
    return `${base}:${this.userId() ?? 'anon'}`;
  }

  private _loadUser(): AppUser | null {
    if (!this.isBrowser) return null;
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AppUser) : null;
  }

  renderGoogleButton(container: HTMLElement): void {
    if (!window.google) {
      setTimeout(() => this.renderGoogleButton(container), 200);
      return;
    }

    if (!this._gisInitialized) {
      window.google.accounts.id.initialize({
        client_id: environment.googleClientId,
        callback: response => this._handleCredential(response.credential),
      });
      this._gisInitialized = true;
    }

    window.google.accounts.id.renderButton(container, {
      theme: 'filled_black',
      size: 'large',
      shape: 'pill',
      text: 'signin_with',
      width: 280,
    });
  }

  /**
   * O código de indicação da URL, se houver.
   *
   * Fica em `sessionStorage` entre o clique no link e o fim do login com o
   * Google, que sai do site e volta: guardar em memória perderia o código
   * exatamente no caminho em que ele é usado. É o único uso de armazenamento
   * aqui, e ele se apaga sozinho ao fechar a aba.
   */
  private _pendingReferral(): string | null {
    if (!this.isBrowser) return null;
    try {
      const daUrl = new URLSearchParams(location.search).get('indicacao');
      if (daUrl) sessionStorage.setItem(REFERRAL_KEY, daUrl);
      return sessionStorage.getItem(REFERRAL_KEY);
    } catch {
      return null;
    }
  }

  private async _handleCredential(idToken: string): Promise<void> {
    const indicacao = this._pendingReferral();
    const res = await firstValueFrom(
      this.http.post<LoginResponse>(`${this.base}/auth/google`, {
        id_token: idToken,
        ...(indicacao ? { referral_code: indicacao } : {}),
      })
    );
    if (this.isBrowser) {
      try {
        sessionStorage.removeItem(REFERRAL_KEY);
      } catch {}
    }
    this._storeTokens(res);
    if (this.isBrowser) localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this._user.set(res.user);
  }

  /**
   * Encerra no servidor antes de limpar o local: sem isso o token continuaria
   * válido até expirar, e "sair" seria só apagar a chave do navegador.
   */
  async logout(allDevices = false): Promise<void> {
    const token = this.token();
    if (token) {
      try {
        await firstValueFrom(
          this.http.post(`${this.base}/auth/logout`, {
            refresh_token: this.refreshToken(),
            all_devices: allDevices,
          })
        );
      } catch {}
    }
    this.clearSession();
  }

  clearSession(): void {
    this._refreshInFlight = null;
    if (!this.isBrowser) return;

    this._clearScopedData();
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    this._user.set(null);
    window.google?.accounts.id.disableAutoSelect();
  }

  private _clearScopedData(): void {
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && SCOPED_KEY_PREFIXES.some(prefix => key.startsWith(prefix))) {
        localStorage.removeItem(key);
      }
    }
  }
}
