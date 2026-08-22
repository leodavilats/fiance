import { AllocationCategory } from './models';

export interface AllocationCategoryOption {
  readonly key: AllocationCategory;
  readonly label: string;
  readonly icon: string;
  readonly desc: string;
}

export const ALLOCATION_CATEGORIES: readonly AllocationCategoryOption[] = [
  { key: 'renda_fixa', label: 'Renda Fixa', icon: 'landmark', desc: 'CDB, LCI, LCA, Tesouro...' },
  { key: 'acoes_br', label: 'Ações BR', icon: 'trending-up', desc: 'Ações da B3' },
  { key: 'bdrs', label: 'BDRs', icon: 'globe', desc: 'BDRs (ações internacionais)' },
  { key: 'fiis', label: 'FIIs', icon: 'building-2', desc: 'Fundos Imobiliários' },
  {
    key: 'etfs',
    label: 'ETFs',
    icon: 'layers',
    desc: 'ETFs (fundos de índice negociados na bolsa)',
  },
];
