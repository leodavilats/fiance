import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
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

interface LoginResponse {
  access_token: string;
  user: AppUser;
}

const TOKEN_KEY = 'fiance_access_token';
const USER_KEY = 'fiance_user';

const SCOPED_KEY_PREFIXES = ['portfolio_renda_fixa'];

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

  private readonly _user = signal<AppUser | null>(this._loadUser());
  readonly user = this._user.asReadonly();

  private _gisInitialized = false;

  isAuthenticated(): boolean {
    const token = this.token();
    if (!token) return false;

    const payload = decodeJwt(token);
    if (!payload?.exp) return true; // sem exp legível: deixa o backend decidir

    return payload.exp * 1000 > Date.now();
  }

  token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
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

  private async _handleCredential(idToken: string): Promise<void> {
    const res = await firstValueFrom(
      this.http.post<LoginResponse>(`${this.base}/auth/google`, { id_token: idToken })
    );
    localStorage.setItem(TOKEN_KEY, res.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this._user.set(res.user);
  }

  logout(): void {
    this._clearScopedData();
    localStorage.removeItem(TOKEN_KEY);
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
