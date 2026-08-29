import { Component, importProvidersFrom } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Lock, LucideAngularModule } from 'lucide-angular';
import { beforeEach, describe, expect, it } from 'vitest';
import { EntitlementService } from '../../core';
import { GateComponent } from './gate.component';

function fakeEntitlements(options: { unrestricted?: boolean; allows?: boolean } = {}) {
  return {
    unrestricted: () => options.unrestricted ?? false,
    allows: () => options.allows ?? false,
    ensureLoaded: () => undefined,
  };
}

@Component({
  standalone: true,
  imports: [GateComponent],
  template: `
    <div class="patrimonio">R$ 128.400,00</div>
    <app-gate feature="strategy" title="Plano de estratégia" [preview]="preview" />
  `,
})
class HostComponent {
  preview = 'Sua maior distância da meta é em FIIs: 8,4 pontos percentuais abaixo do alvo.';
}

function render(options: { unrestricted?: boolean; allows?: boolean } = {}) {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      importProvidersFrom(LucideAngularModule.pick({ Lock })),
      { provide: EntitlementService, useValue: fakeEntitlements(options) },
    ],
  });
  const fixture = TestBed.createComponent(HostComponent);
  fixture.detectChanges();
  return fixture;
}

describe('gate contextual', () => {
  beforeEach(() => TestBed.resetTestingModule());

  describe('quando aparece', () => {
    it('some com a régua desligada', () => {
      const fixture = render({ unrestricted: true });

      expect(fixture.nativeElement.querySelector('[role="region"]')).toBeNull();
    });

    it('some quando a pessoa já tem o direito', () => {
      const fixture = render({ unrestricted: false, allows: true });

      expect(fixture.nativeElement.querySelector('[role="region"]')).toBeNull();
    });

    it('aparece quando falta o direito', () => {
      const fixture = render({ unrestricted: false, allows: false });

      expect(fixture.nativeElement.querySelector('[role="region"]')).not.toBeNull();
    });
  });

  describe('nunca desfoca dado do usuário', () => {
    it('não aplica desfoque a nada', () => {
      const fixture = render();
      const html: string = fixture.nativeElement.innerHTML;

      expect(html).not.toMatch(/blur/i);
      expect(html).not.toMatch(/backdrop-filter/i);
    });

    it('não cobre conteúdo: não há sobreposição', () => {
      const fixture = render();
      const html: string = fixture.nativeElement.innerHTML;

      expect(html).not.toMatch(/\babsolute\b/);
      expect(html).not.toMatch(/\bfixed\b/);
      expect(html).not.toMatch(/z-\d/);
    });

    it('o patrimônio ao lado continua legível', () => {
      const fixture = render();

      const patrimonio = fixture.nativeElement.querySelector('.patrimonio');
      expect(patrimonio.textContent).toContain('128.400,00');
    });
  });

  describe('a prévia é o argumento', () => {
    it('mostra o número verdadeiro da carteira quando ele existe', () => {
      const fixture = render();

      expect(fixture.nativeElement.textContent).toContain('8,4 pontos percentuais');
    });

    it('funciona sem prévia, sem quebrar', () => {
      TestBed.resetTestingModule();
      TestBed.configureTestingModule({
        providers: [
          provideRouter([]),
          importProvidersFrom(LucideAngularModule.pick({ Lock })),
          { provide: EntitlementService, useValue: fakeEntitlements() },
        ],
      });
      const fixture = TestBed.createComponent(GateComponent);
      fixture.componentRef.setInput('feature', 'strategy');
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('[role="region"]')).not.toBeNull();
    });
  });

  describe('acessibilidade', () => {
    it('é uma região nomeada, não um bloco anônimo', () => {
      const fixture = render();
      const regiao = fixture.nativeElement.querySelector('[role="region"]');

      expect(regiao.getAttribute('aria-label')).toContain('Plano de estratégia');
    });

    it('o ícone de cadeado é decorativo', () => {
      const fixture = render();
      const icone = fixture.nativeElement.querySelector('lucide-icon');

      expect(icone.getAttribute('aria-hidden')).toBe('true');
    });
  });
});
