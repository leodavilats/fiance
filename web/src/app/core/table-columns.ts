import { PositionSortColumn } from './services/carteira-store.service';

export interface PositionColumn {
  readonly id: PositionSortColumn | 'current_value' | 'weight' | 'margin';
  readonly label: string;
  readonly hint: string;
  readonly align: 'left' | 'right';
  readonly sortable: boolean;
  readonly essential: boolean;

  readonly byDefault: boolean;
}

export const POSITION_COLUMNS: readonly PositionColumn[] = [
  {
    id: 'ticker',
    label: 'Ativo',
    hint: 'Código de negociação',
    align: 'left',
    sortable: true,
    essential: true,
    byDefault: true,
  },
  {
    id: 'asset_type',
    label: 'Tipo',
    hint: 'Classe do ativo',
    align: 'left',
    sortable: true,
    essential: false,
    byDefault: true,
  },
  {
    id: 'quantity',
    label: 'Qtd',
    hint: 'Quantidade em carteira',
    align: 'right',
    sortable: true,
    essential: false,
    byDefault: true,
  },
  {
    id: 'avg_price',
    label: 'P. médio',
    hint: 'Preço médio pago',
    align: 'right',
    sortable: true,
    essential: false,
    byDefault: true,
  },
  {
    id: 'current_price',
    label: 'Atual',
    hint: 'Cotação mais recente',
    align: 'right',
    sortable: true,
    essential: false,
    byDefault: true,
  },
  {
    id: 'current_value',
    label: 'Valor',
    hint: 'Quantidade × cotação atual',
    align: 'right',
    sortable: true,
    essential: true,
    byDefault: true,
  },
  {
    id: 'weight',
    label: 'Peso',
    hint: 'Participação da posição no total negociado',
    align: 'right',
    sortable: false,
    essential: false,
    byDefault: true,
  },
  {
    id: 'fair_price',
    label: 'Justo',
    hint: 'Consenso dos métodos de valuation aplicáveis',
    align: 'right',
    sortable: true,
    essential: false,
    byDefault: false,
  },
  {
    id: 'margin',
    label: 'Margem',
    hint: 'Distância entre o preço atual e o preço justo',
    align: 'right',
    sortable: false,
    essential: false,
    byDefault: false,
  },
  {
    id: 'pnl_pct',
    label: 'Rend.',
    hint: 'Resultado da posição em percentual',
    align: 'right',
    sortable: true,
    essential: false,
    byDefault: true,
  },
  {
    id: 'verdict',
    label: 'Leitura',
    hint: 'Veredito do sistema para o ativo',
    align: 'left',
    sortable: true,
    essential: false,
    byDefault: true,
  },
];

export const DEFAULT_POSITION_COLUMNS: readonly string[] = POSITION_COLUMNS.filter(
  c => c.byDefault
).map(c => c.id);

export function parseColumns(raw: string | null): string[] {
  const known = new Set(POSITION_COLUMNS.map(c => c.id as string));
  const essential = POSITION_COLUMNS.filter(c => c.essential).map(c => c.id as string);

  const requested = (raw ?? '')
    .split(',')
    .map(s => s.trim())
    .filter(s => known.has(s));

  const chosen = requested.length > 0 ? requested : [...DEFAULT_POSITION_COLUMNS];
  for (const id of essential) {
    if (!chosen.includes(id)) chosen.push(id);
  }
  return POSITION_COLUMNS.filter(c => chosen.includes(c.id as string)).map(c => c.id as string);
}
