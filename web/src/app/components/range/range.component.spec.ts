import { registerLocaleData } from '@angular/common';
import localePt from '@angular/common/locales/pt';
import { Component, LOCALE_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';
import { RangeComponent } from './range.component';

registerLocaleData(localePt);

@Component({
  standalone: true,
  imports: [RangeComponent],
  template: `
    <dl>
      <div
        appRange
        label="Carteira em 60 meses"
        [low]="low"
        [high]="high"
        [base]="base"
        [cents]="cents"
      ></div>
    </dl>
  `,
})
class HostComponent {
  low = 120_000;
  high = 190_000;
  base: number | null = 150_000;
  cents = false;
}

function render(over: Partial<HostComponent> = {}) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({ providers: [{ provide: LOCALE_ID, useValue: 'pt-BR' }] });
  const fixture = TestBed.createComponent(HostComponent);
  Object.assign(fixture.componentInstance, over);
  fixture.detectChanges();
  return fixture;
}

describe('faixa de projeção', () => {
  it('o número projetado sai como faixa, nunca sozinho', () => {
    const texto: string = render().nativeElement.textContent;

    expect(texto).toContain('entre R$');
    expect(texto).toContain('120.000');
    expect(texto).toContain('190.000');
  });

  it('o cenário base é legenda sob a faixa, e não o lugar dela', () => {
    const fixture = render();
    const valores = [...fixture.nativeElement.querySelectorAll('dd')].map(
      (d: Element) => d.textContent?.trim() ?? ''
    );

    expect(valores[0], 'a primeira cifra que se lê é a faixa').toContain('entre R$');
    expect(valores[1]).toContain('cenário base');
    expect(valores[1]).toContain('150.000');
  });

  it('sem cenário base a legenda some, em vez de sair zerada', () => {
    const texto: string = render({ base: null }).nativeElement.textContent;

    expect(texto).not.toContain('cenário base');
    expect(texto).not.toContain('R$ 0');
  });

  it('renda mensal se lê em centavos; patrimônio a cinco anos, não', () => {
    expect(render({ cents: false }).nativeElement.textContent).toContain('120.000');
    expect(
      render({ low: 1234.5, high: 2000, base: null, cents: true }).nativeElement.textContent
    ).toContain('1.234,50');
  });

  it('é dt/dd dentro do dl, senão o leitor de tela perde o par rótulo/cifra', () => {
    const dl = render().nativeElement.querySelector('dl');

    expect(dl.querySelector('dt')?.textContent).toContain('Carteira em 60 meses');
    expect(
      dl.querySelector(':scope > app-range'),
      'um elemento entre o dl e o par quebraria a lista de definição'
    ).toBeNull();
  });
});
