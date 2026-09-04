import { Component } from '@angular/core';
import { IncomeCompareComponent } from '../market/income-compare/income-compare.component';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { RendaFixaComponent } from '../market/renda-fixa/renda-fixa.component';

@Component({
  selector: 'app-renda-fixa-page',
  standalone: true,
  imports: [PageHeaderComponent, RendaFixaComponent, IncomeCompareComponent],
  template: `
    <app-page-header
      title="Renda fixa"
      question="Quanto rende um título, e rende mais que a bolsa para o meu caso?"
    />

    <div class="space-y-6">
      <app-renda-fixa />
      <app-income-compare />
    </div>
  `,
})
export class RendaFixaPageComponent {}
