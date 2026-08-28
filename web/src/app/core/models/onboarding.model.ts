/** Estado do onboarding, derivado no servidor do que a pessoa já fez. */
export interface OnboardingState {
  step: number;
  total_steps: number;
  completed: boolean;
  onboarded_at: number | null;
  positions: number;
  has_goals: boolean;
  /** Por que o passo é este — a tela mostra em vez de só uma barra. */
  reason: string;
}

export interface DemoPortfolioResponse {
  is_demo: true;
  disclaimer: string;
  evaluation: unknown;
}
