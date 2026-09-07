import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  CashEntry,
  CashEntryPayload,
  CashMonth,
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
