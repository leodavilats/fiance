import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class LoadingService {
  private _loading = signal(false);
  private _activeRequests = 0;
  private _autoResetTimer: any = null;
  readonly loading = this._loading.asReadonly();

  show(): void {
    this._activeRequests++;
    this._loading.set(true);
    
    this.clearAutoReset();
    this._autoResetTimer = setTimeout(() => {
      this.reset();
    }, 65000);
  }

  hide(): void {
    this._activeRequests--;
    
    if (this._activeRequests <= 0) {
      this._activeRequests = 0;
      this._loading.set(false);
      this.clearAutoReset();
    }
  }

  reset(): void {
    this._activeRequests = 0;
    this._loading.set(false);
    this.clearAutoReset();
  }

  private clearAutoReset(): void {
    if (this._autoResetTimer) {
      clearTimeout(this._autoResetTimer);
      this._autoResetTimer = null;
    }
  }
}
