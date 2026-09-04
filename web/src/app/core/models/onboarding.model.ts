export interface OnboardingState {
  step: number;
  total_steps: number;
  completed: boolean;
  onboarded_at: number | null;
  positions: number;
  has_goals: boolean;

  reason: string;
}

export interface DemoPortfolioResponse {
  is_demo: true;
  disclaimer: string;
  evaluation: unknown;
}
