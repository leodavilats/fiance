import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  CashEntry,
  CashEntryPayload,
  CashMonth,
  CashMonthTemplate,
  CashVocabulary,
  Debt,
  DebtPayload,
  Surplus,
} from '../models/cashflow.model';

@Injectable({ providedIn: 'root' })
export class CashflowService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  vocabulary(): Observable<CashVocabulary> {
    return this.http.get<CashVocabulary>(`${this.base}/cashflow/vocabulary`);
  }

  month(month?: string): Observable<CashMonth> {
    const params = month ? new HttpParams().set('month', month) : undefined;
    return this.http.get<CashMonth>(`${this.base}/cashflow/month`, { params });
  }

  entries(): Observable<CashEntry[]> {
    return this.http.get<CashEntry[]>(`${this.base}/cashflow/entries`);
  }

  addEntry(payload: CashEntryPayload): Observable<CashEntry> {
    return this.http.post<CashEntry>(`${this.base}/cashflow/entries`, payload);
  }

  addEntries(entries: CashEntryPayload[]): Observable<CashEntry[]> {
    return this.http.post<CashEntry[]>(`${this.base}/cashflow/entries/batch`, { entries });
  }

  updateEntry(entryId: number, payload: CashEntryPayload): Observable<CashEntry> {
    return this.http.put<CashEntry>(`${this.base}/cashflow/entries/${entryId}`, payload);
  }

  /** O mês anterior lido como molde do destino. Leitura: não grava nada. */
  monthTemplate(target: string, source?: string): Observable<CashMonthTemplate> {
    let params = new HttpParams().set('target', target);
    if (source) params = params.set('source', source);
    return this.http.get<CashMonthTemplate>(`${this.base}/cashflow/month/template`, { params });
  }

  markPaid(entryId: number, paidOn?: string): Observable<void> {
    return this.http.post<void>(`${this.base}/cashflow/entries/${entryId}/paid`, {
      paid_on: paidOn ?? null,
    });
  }

  deleteEntry(entryId: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/cashflow/entries/${entryId}`);
  }

  debts(): Observable<Debt[]> {
    return this.http.get<Debt[]>(`${this.base}/cashflow/debts`);
  }

  addDebt(payload: DebtPayload): Observable<Debt> {
    return this.http.post<Debt>(`${this.base}/cashflow/debts`, payload);
  }

  settleDebt(debtId: number): Observable<void> {
    return this.http.post<void>(`${this.base}/cashflow/debts/${debtId}/settled`, {});
  }

  /** A ponte: o mês projetado e a ordem do que fazer com o piso da sobra. */
  surplus(month?: string): Observable<Surplus> {
    const params = month ? new HttpParams().set('month', month) : undefined;
    return this.http.get<Surplus>(`${this.base}/surplus`, { params });
  }
}
