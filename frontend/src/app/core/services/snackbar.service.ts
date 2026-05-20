import { Injectable, signal } from '@angular/core';

export interface SnackbarMessage {
  id: number;
  message: string;
  type: 'error' | 'success' | 'info';
}

@Injectable({ providedIn: 'root' })
export class SnackbarService {
  private _messages = signal<SnackbarMessage[]>([]);
  readonly messages = this._messages.asReadonly();
  private idCounter = 0;

  showError(message: string): void {
    this.show(message, 'error');
  }

  showSuccess(message: string): void {
    this.show(message, 'success');
  }

  showInfo(message: string): void {
    this.show(message, 'info');
  }

  private show(message: string, type: 'error' | 'success' | 'info'): void {
    const id = this.idCounter++;
    const msg: SnackbarMessage = { id, message, type };
    this._messages.update(msgs => [...msgs, msg]);
    
    setTimeout(() => this.remove(id), 5000);
  }

  remove(id: number): void {
    this._messages.update(msgs => msgs.filter(m => m.id !== id));
  }
}
