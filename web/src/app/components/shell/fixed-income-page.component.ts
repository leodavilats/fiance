import { Component } from '@angular/core';
import { IncomeCompareComponent } from '../market/income-compare/income-compare.component';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { FixedIncomeComponent } from '../market/fixed-income/fixed-income.component';

@Component({
  selector: 'app-fixed-income-page',
  standalone: true,
  imports: [PageHeaderComponent, FixedIncomeComponent, IncomeCompareComponent],
  template: `
    <app-page-header
      title="Renda fixa"
      question="Quanto rende um título, e rende mais que a bolsa para o meu caso?"
    />

    <div class="space-y-6">
      <app-fixed-income />
      <app-income-compare />
    </div>
  `,
})
export class FixedIncomePageComponent {}
