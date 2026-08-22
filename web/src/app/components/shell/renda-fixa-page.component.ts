import { Component } from '@angular/core';
import { IncomeCompareComponent } from '../market/income-compare/income-compare.component';
import { RendaFixaComponent } from '../market/renda-fixa/renda-fixa.component';

@Component({
  selector: 'app-renda-fixa-page',
  standalone: true,
  imports: [RendaFixaComponent, IncomeCompareComponent],
  template: `
    <div class="space-y-6">
      <app-renda-fixa />
      <app-income-compare />
    </div>
  `,
})
export class RendaFixaPageComponent {}
