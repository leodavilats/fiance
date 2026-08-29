import { describe, expect, it } from 'vitest';
import {
  fiCategoriaApelidos,
  fiCategorias,
  fiClasseChipDaSerie,
  fiClasseTextoDaSerie,
  fiSetorApelidos,
  fiSetorSeriePorRotulo,
  fiSetores,
  fiTiposDeAtivo,
} from './vocabulary';

describe('vocabulário gerado', () => {
  describe('categoria e tipo de ativo são a mesma coisa vista de dois lados', () => {
    it('todo tipo de ativo aponta para uma categoria que existe', () => {
      for (const [id, tipo] of Object.entries(fiTiposDeAtivo)) {
        expect(fiCategorias[tipo.category], `${id} → ${tipo.category}`).toBeDefined();
      }
    });

    it('todo apelido de categoria aponta para uma categoria que existe', () => {
      for (const [de, para] of Object.entries(fiCategoriaApelidos)) {
        expect(fiCategorias[para], `${de} → ${para}`).toBeDefined();
      }
    });
  });

  describe('setor', () => {
    it('cada setor canônico tem uma série própria', () => {
      const series = Object.values(fiSetores).map(s => s.series);

      expect(new Set(series).size).toBe(series.length);
    });

    it('o mapa por rótulo cobre todos os setores canônicos', () => {
      for (const setor of Object.values(fiSetores)) {
        expect(fiSetorSeriePorRotulo[setor.label], setor.label).toBe(setor.series);
      }
    });

    it('todo apelido de setor cai num rótulo conhecido', () => {
      const rotulos = new Set([...Object.values(fiSetores).map(s => s.label), 'Outros']);

      for (const [de, para] of Object.entries(fiSetorApelidos)) {
        expect(rotulos.has(para), `${de} → ${para}`).toBe(true);
      }
    });
  });

  describe('classes do Tailwind', () => {
    it('são literais, porque o scanner não resolve interpolação', () => {
      for (const classe of Object.values(fiClasseTextoDaSerie)) {
        expect(classe).toMatch(/^text-series-(\d+|other)$/);
      }
    });

    it('o chip carrega o modificador de opacidade no próprio literal', () => {
      for (const classe of Object.values(fiClasseChipDaSerie)) {
        expect(classe).toMatch(/^bg-series-(\d+|other)\/15$/);
      }
    });

    it('toda categoria tem classe para a própria série', () => {
      for (const [id, categoria] of Object.entries(fiCategorias)) {
        expect(fiClasseTextoDaSerie[categoria.series], id).toBeDefined();
        expect(fiClasseChipDaSerie[categoria.series], id).toBeDefined();
      }
    });
  });
});
