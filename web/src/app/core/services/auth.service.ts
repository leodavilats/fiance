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

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  private readonly _user = signal<AppUser | null>(this._loadUser());
  readonly user = this._user.asReadonly();

  private _gisInitialized = false;
  private _refreshInFlight: Promise<boolean> | null = null;

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
