import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { FairPriceComponent } from './fair-price.component';

function render(props: Partial<Record<string, unknown>>): string {
  const fixture = TestBed.createComponent(FairPriceComponent);
  for (const [chave, valor] of Object.entries(props)) {
    fixture.componentRef.setInput(chave, valor);
  }
  fixture.detectChanges();
  return (fixture.nativeElement as HTMLElement).textContent?.replace(/\s+/g, ' ').trim() ?? '';
}

describe('preço justo', () => {
  beforeEach(() => TestBed.resetTestingModule());

  it('a cifra nunca sai sem dizer quantos métodos a formaram', () => {
    const saida = render({ value: 32.1, methods: 3 });

    // O separador decimal segue o locale registrado, e no ambiente de teste ele nao e o pt-BR.
    expect(saida, 'o número tem de aparecer').toMatch(/32[.,]10/);
    expect(saida, 'preço justo sem a base é um número de autoridade desconhecida').toContain(
      '3 métodos'
    );
  });

  it('um método só se nomeia, em vez de posar de consenso', () => {
    const saida = render({ value: 18.4, method: 'Bazin' });

    expect(saida, 'Bazin sozinho é Bazin, não consenso').toContain('por Bazin');
    expect(saida).not.toContain('consenso');
  });

  it('a ausência é uma razão nomeada, nunca um traço', () => {
    const saida = render({ value: null, absent: 'sem histórico de proventos' });

    expect(saida).toBe('sem histórico de proventos');
    expect(saida, 'traço faz a pessoa achar que o produto não olhou').not.toContain('—');
  });

  it('sem razão informada, a ausência ainda diz o que faltou', () => {
    expect(render({ value: null })).toBe('sem preço justo');
  });
});
