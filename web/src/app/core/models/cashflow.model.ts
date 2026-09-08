export type CashKind = 'income' | 'expense';

export type DebtClass = 'expensive' | 'manageable' | 'no_rate';

export type CascadeStepType = 'debt' | 'reserve' | 'contribution';

export interface CashEntry {
  id: number;
  kind: CashKind;
  category: string;
  description: string;
  amount: number;
  due_on: string;
  paid_on: string | null;

  /** Derivado do razão — provento creditado. Não é editável no caixa. */
  derived: boolean;
}

export interface CashEntryPayload {
  kind: CashKind;
  category: string;
  description: string;
  amount: number;
  due_on: string;
  paid_on?: string | null;
}

export interface CashTemplateCandidate {
  kind: CashKind;
  category: string;
  description: string;
  amount: number;

  /** Já no mês de destino, preso ao último dia quando o mês é mais curto. */
  due_on: string;

  /** Se a categoria volta todo mês por natureza. Gasto variável não volta. */
  repeats: boolean;

  already_there: boolean;
}

export interface CashMonthTemplate {
  source: string;
  target: string;
  candidates: CashTemplateCandidate[];
}

export interface CashEstimate {
  base_months: string[];
  expected_low: number;
  expected_high: number;
  spent_so_far: number;
  remaining_low: number;
  remaining_high: number;
}

export interface CashDueEntry {
  id: number | null;
  category: string;
  description: string;
  amount: number;
  due_on: string;
}

export interface CashMonth {
  month: string;
  received: number;
  paid: number;
  committed: number;

  /** Fato: entrou, menos saiu, menos o comprometido e datado. Não tem faixa. */
  free_now: number;

  /** Projeção: o piso da sobra, e o número sobre o qual a ordem decide. */
  surplus_low: number;
  surplus_high: number;

  /** Falso quando não há mês fechado para estimar. Ausência não vira zero. */
  has_range: boolean;

  income_baseline: number;
  estimate: CashEstimate;
  due: CashDueEntry[];
}

export interface Debt {
  id: number | null;
  kind: string;
  description: string;
  balance: number;
  monthly_rate: number | null;
  class: DebtClass;
  reference_monthly: number | null;
  reference_source: string;

  /** A taxa em que o veredito muda. Sai por álgebra, não por opinião. */
  flip_rate: number | null;
}

export interface DebtPayload {
  kind: string;
  description: string;
  balance: number;
  monthly_rate?: number | null;
}

export interface CascadeStep {
  order: number;
  type: CascadeStepType;
  amount: number;
  reason: string;
  falsifier: string | null;
  reference: string | null;
}

export interface Cascade {
  surplus_low: number;
  steps: CascadeStep[];
  available_to_invest: number;
}

export interface Surplus {
  month: CashMonth;
  cascade: Cascade;

  /** Falso quando não há lançamento próprio: a tela pede o valor e diz por quê. */
  has_cash: boolean;
}

export interface CashVocabulary {
  expense_categories: string[];
  income_categories: string[];
  debt_kinds: string[];
}
