import 'package:dio/dio.dart';

enum Estado { conteudo, carregando, falha, isEmpty }

const telasDoApp = <String, String>{
  'login': '/login',
  'mes': '/mes',
  'mes-avisos': '/mes/avisos',
  'mes-dividas': '/mes/dividas',
  'sobra': '/sobra',
  'sobra-desvio': '/sobra/desvio',
  'patrimonio': '/patrimonio',
  'patrimonio-renda-fixa': '/patrimonio/renda-fixa',
  'patrimonio-razao': '/patrimonio/razao',
  'patrimonio-razao-importar': '/patrimonio/razao/importar',
  'patrimonio-razao-importar-b3': '/patrimonio/razao/importar/b3',
  'patrimonio-razao-conferir': '/patrimonio/razao/conferir',
  'patrimonio-proventos': '/patrimonio/proventos',
  'patrimonio-seguidas': '/patrimonio/seguidas',
  'descobrir': '/descobrir',
  'voce': '/voce',
  'voce-objetivos': '/voce/objetivos',
  'voce-comecar': '/voce/comecar',
  'voce-conta': '/voce/conta',
  'voce-conta-excluir': '/voce/conta/excluir',
  'voce-conta-importar': '/voce/conta/importar',
  'voce-notificacoes': '/voce/avisos',
  'voce-investir': '/voce/investir',
  'sobra-aporte': '/sobra/aporte',
  'patrimonio-projecao': '/patrimonio/projecao',
  'ativo': '/ativo/ITSA4',
};

class RedeDublada extends Interceptor {
  RedeDublada(this.estado);

  final Estado estado;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (estado == Estado.carregando) return;

    if (estado == Estado.falha) {
      handler.reject(
        DioException(
          requestOptions: options,
          response: Response<dynamic>(requestOptions: options, statusCode: 503),
          type: DioExceptionType.badResponse,
        ),
      );
      return;
    }

    handler.resolve(
      Response<dynamic>(
        requestOptions: options,
        statusCode: 200,
        data: _resposta(options.path, estado),
      ),
    );
  }
}

dynamic _resposta(String caminho, Estado estado) {
  final isEmpty = estado == Estado.isEmpty;

  if (caminho.contains('/preferences')) {
    return {
      'risk_profile': 'moderate',
      'passive_income_goal': isEmpty ? null : 5000.0,
      'preferred_categories': <String>[],
      'preferred_sectors': <String>[],
      'excluded_tickers': <String>[],
      'detail_level': 'completo',
      'desired_yield_stock': 0.06,
      'desired_yield_fii': 0.10,
      'desired_yield_bdr': 0.04,
      'desired_yield_etf': 0.04,
    };
  }

  if (caminho.contains('/auth/me')) {
    return {'id': 'demo', 'name': 'Maria', 'email': 'maria@exemplo.com'};
  }

  if (caminho.contains('/inbox/unread') || caminho.contains('/inbox/read')) {
    return {'unread': isEmpty ? 0 : 2};
  }

  if (caminho.contains('/inbox')) {
    final agora = DateTime.now().millisecondsSinceEpoch / 1000;
    return {
      'items': isEmpty
          ? <Object>[]
          : [
              {
                'id': 3,
                'kind': 'price_alert',
                'severity': 'warning',
                'title': 'PETR4 está abaixo de R\$ 30,00',
                'detail': 'O preço chegou a R\$ 29,80, e o alerta que você criou disparou.',
                'ticker': 'PETR4',
                'action': 'analyze',
                'action_label': 'Ver PETR4',
                'created_at': agora - 2 * 3600,
                'read_at': null,
              },
              {
                'id': 2,
                'kind': 'maturity',
                'severity': 'warning',
                'title': 'LCI Inter vence em 20 dias',
                'detail': 'R\$ 8.492,10 vão voltar para o caixa — decida onde reaplicar antes disso.',
                'action': 'fixed_income',
                'action_label': 'Ver renda fixa',
                'created_at': agora - 26 * 3600,
                'read_at': null,
              },
              {
                'id': 1,
                'kind': 'allocation',
                'severity': 'warning',
                'title': 'Ações BR está 9 pontos acima da meta',
                'detail': 'Atual 54% contra meta de 45%. São 2 categoria(s) fora da faixa.',
                'action': 'rebalance',
                'action_label': 'Rebalancear',
                'created_at': agora - 9 * 86400,
                'read_at': agora - 8 * 86400,
              },
            ],
      'unread': isEmpty ? 0 : 2,
      'next_cursor': null,
      'has_more': false,
    };
  }

  const listas = [
    '/goals',
    '/sector-goals',
    '/alerts',
    '/cashflow/debts',
    '/cashflow/entries',
  ];
  if (listas.any(caminho.contains)) {
    return isEmpty ? <dynamic>[] : _cheio(caminho);
  }

  if (caminho.startsWith('/asset/')) return analiseDeAcao;

  if (caminho.contains('/income-compare')) {
    return {
      'amount': 10000.0,
      'horizon_months': 12,
      'cdi_anual': 11.15,
      'ipca_anual': 4.4,
      'fixed_income': isEmpty
          ? <Object>[]
          : [
              {
                'kind': 'renda_fixa',
                'label': 'CDB 110% do CDI',
                'net_income_yield_pct': 10.42,
                'income_basis': 'Oferta de referência para 12 meses, já descontados 17,5% de IR.',
                'has_upside': false,
                'liquidity': 'no_vencimento',
                'tax_note': 'IR de 17,5% no prazo',
                'risk_note': 'Coberto pelo Fundo Garantidor de Créditos (FGC) até R\$ 250 mil.',
                'monthly_income_estimate': 86.83,
              },
            ],
      'assets': isEmpty
          ? <Object>[]
          : [
              {
                'kind': 'fii',
                'label': 'MXRF11',
                'ticker': 'MXRF11',
                'net_income_yield_pct': 12.1,
                'income_basis': 'Proventos dos últimos 12 meses sobre o preço de hoje.',
                'has_upside': true,
                'liquidity': 'bolsa',
                'tax_note': 'Isento para pessoa física',
                'risk_note': '',
                'monthly_income_estimate': 100.83,
              },
            ],
      'verdict': isEmpty ? '' : 'O fundo imobiliário rende mais em proventos, e o preço oscila.',
      'disclaimer': 'Ferramenta de análise, não consultoria.',
    };
  }

  if (caminho.contains('/fixed-income') && isEmpty) {
    return {
      ..._vazio(),
      'total_investido': 0.0,
      'total_atual': 0.0,
      'total_rendimento': 0.0,
      'rendimento_pct': 0.0,
      'taxa_media_aa': 0.0,
      'cdi_referencia': 0.0,
      'fonte_taxas': 'bcb',
    };
  }

  if (caminho.contains('/dashboard') && isEmpty) {
    return {
      ..._vazio(),
      'summary': {
        'total_invested': 0.0,
        'total_current': 0.0,
        'total_pnl': 0.0,
        'total_pnl_pct': 0.0,
        'monthly_dividends_estimate': 0.0,
        'passive_income_goal': null,
        'passive_income_progress': null,
        'positions_count': 0,
      },
      'top_buys': <dynamic>[],
      'top_sells': <dynamic>[],
      'alerts': <dynamic>[],
    };
  }

  if (caminho.contains('/transactions/reconciliation')) {
    return {
      'positions': isEmpty ? 3 : 4,
      'projected': 3,
      'in_sync': isEmpty,
      'differences': isEmpty
          ? <dynamic>[]
          : [
              {
                'ticker': 'ITSA4',
                'reason': 'posicao_sem_razao',
                'stored': {'ticker': 'ITSA4', 'quantity': 300.0, 'avg_price': 9.84},
                'projected': null,
              },
              {
                'ticker': 'PETR4',
                'reason': 'quantidade',
                'stored': {'ticker': 'PETR4', 'quantity': 180.0, 'avg_price': 38.42},
                'projected': {'symbol': 'PETR4', 'quantity': 200.0, 'avg_price': 38.42},
              },
            ],
    };
  }

  if (caminho.contains('/suggestions/followed')) {
    if (isEmpty) {
      return {
        ..._vazio(),
        'summary': 'Nenhuma sugestão marcada como seguida ainda. Ao registrar as que você '
            'executar, esta tela mostra o resultado — e você pode auditar o produto.',
      };
    }
    return {
      'items': [
        {
          'id': 1,
          'ticker': 'BBAS3',
          'source': 'opportunities',
          'action': 'comprar',
          'quantity': 100.0,
          'price': 24.10,
          'followed_on': '2026-06-02',
          'entry_id': 7,
          'invested': 2410.0,
          'current_value': 2688.0,
          'pnl': 278.0,
          'pnl_pct': 11.54,
          'days_held': 116,
          'ibov_pct_since': 4.2,
          'beat_ibov': true,
          'score_at_suggestion': 78.0,
        },
      ],
      'total_invested': 2410.0,
      'total_current_value': 2688.0,
      'total_pnl': 278.0,
      'total_pnl_pct': 11.54,
      'ibov_pct_same_period': 4.2,
      'beat_ibov': true,
      'by_source': <dynamic>[],
      'summary': 'A 1 compra que você fez a partir de sugestões está +11,5% contra +4,2% do '
          'Ibovespa no período — acima do índice.',
      'total_count': 1,
      'has_more': false,
    };
  }

  if (caminho.contains('/onboarding')) {
    return {
      'step': isEmpty ? 2 : 3,
      'total_steps': 3,
      'completed': false,
      'positions': isEmpty ? 0 : 6,
      'has_goals': false,
      'reason': isEmpty
          ? 'Falta registrar a primeira posição.'
          : 'Falta definir a primeira meta de alocação.',
    };
  }

  return isEmpty ? _vazio() : _cheio(caminho);
}

Map<String, dynamic> _vazio() => {
  'items': <dynamic>[],
  'count': 0,
  'entries': <dynamic>[],
  'positions': <dynamic>[],
  'allocations': <dynamic>[],
  'snapshots': <dynamic>[],
  'steps': <dynamic>[],
  'goals': <dynamic>[],
  'suggestions': <dynamic>[],
  'debts': <dynamic>[],
  'months': <dynamic>[],
  'by_month': <dynamic>[],
  'by_ticker': <dynamic>[],
  'allocation_gaps': <dynamic>[],
};

Map<String, dynamic> _posicao(
  String ticker,
  String nome,
  double quantidade,
  double medio,
  double current,
  String veredito,
  String rotulo,
  String categoria,
  String setor,
  double dy,
) {
  final investido = quantidade * medio;
  final valor = quantidade * current;
  return {
    'ticker': ticker,
    'name': nome,
    'asset_type': categoria == 'fiis' ? 'fii' : 'br_stock',
    'quantity': quantidade,
    'avg_price': medio,
    'current_price': current,
    'invested': investido,
    'current_value': valor,
    'pnl': valor - investido,
    'pnl_pct': (valor - investido) / investido * 100,
    'verdict': veredito,
    'label': rotulo,
    'category_resolved': categoria,
    'dividend_yield': dy,
    'sector': setor,
    'as_of': 1789324890.0,
    'reasons': <String>[],
    'confidence': 0.75,
    'data_years': 5,
    'independent_inputs': 1,
    'trend_basis': 'long',
  };
}

dynamic _cheio(String caminho) {
  final base = _vazio();

  if (caminho.contains('/dashboard')) {
    return {
      ...base,
      'summary': {
        'total_invested': 84200.00,
        'total_current': 97430.55,
        'total_pnl': 13230.55,
        'total_pnl_pct': 15.71,
        'monthly_dividends_estimate': 412.80,
        'passive_income_goal': 5000.0,
        'passive_income_progress': 8.26,
        'positions_count': 6,
        'dividends_received_last_12m': 4211.30,
      },
      'positions': [
        _posicao('PETR4', 'Petróleo Brasileiro', 300, 32.10, 38.42, 'BUY', 'Abaixo do preço justo', 'acoes_br',
            'Energia', 9.8),
        _posicao('BBAS3', 'Banco do Brasil', 400, 21.40, 22.49, 'STRONG_BUY',
            'Bem abaixo do preço justo', 'acoes_br', 'Bancos', 11.2),
        _posicao('MXRF11', 'Maxi Renda', 900, 9.80, 9.14, 'HOLD', 'No preço justo', 'fiis',
            'Fundos imobiliários', 12.8),
        _posicao('WEGE3', 'WEG', 120, 44.10, 51.49, 'UNKNOWN', 'Sem preço justo',
            'acoes_br', 'Bens industriais', 1.9),
      ],
      'allocations': [
        {'category': 'acoes_br', 'current_value': 52300.0, 'current_pct': 53.7, 'target_pct': 45.0},
        {'category': 'fiis', 'current_value': 24130.55, 'current_pct': 24.8, 'target_pct': 25.0},
        {'category': 'renda_fixa', 'current_value': 18000.0, 'current_pct': 18.5, 'target_pct': 25.0},
        {'category': 'etfs', 'current_value': 3000.0, 'current_pct': 3.0, 'target_pct': 5.0},
      ],
      'top_buys': <dynamic>[],
      'top_sells': <dynamic>[],
      'alerts': <dynamic>[],
      'health': {
        'score': 68.0,
        'concentration_score': 62.0,
        'sector_concentration_score': 58.0,
        'diversification_score': 74.0,
        'risk_score': 70.0,
        'top_position_ticker': 'PETR4',
        'top_position_pct': 11.8,
        'top_sector': 'Energia',
        'top_sector_pct': 22.4,
        'warnings': <dynamic>[],
      },
      'snapshots': [
        {
          'captured_at': 1782000000,
          'total_invested': 71000.0,
          'total_current': 76200.0,
          'total_pnl': 5200.0,
          'total_pnl_pct': 7.32,
        },
        {
          'captured_at': 1784678400,
          'total_invested': 78400.0,
          'total_current': 85100.0,
          'total_pnl': 6700.0,
          'total_pnl_pct': 8.55,
        },
        {
          'captured_at': 1787356800,
          'total_invested': 84200.0,
          'total_current': 97430.55,
          'total_pnl': 13230.55,
          'total_pnl_pct': 15.71,
        },
      ],
    };
  }

  if (caminho.contains('/fixed-income')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'nome': 'CDB Banco Master',
          'tipo': 'cdb',
          'valor_investido': 10000.0,
          'taxa': 118.0,
          'tipo_taxa': 'pos_fixado',
          'percentual_cdi': 118.0,
          'data_aplicacao': '2025-09-10',
          'vencimento': '2027-09-10',
          'liquidez': 'no_vencimento',
          'isento_ir': false,
          'oculto': false,
          'valor_atual': 11240.30,
          'rendimento_acumulado': 1240.30,
          'rendimento_pct': 12.40,
          'meses_decorridos': 12,
          'taxa_anual_efetiva_pct': 13.2,
          'yield_equivalente_pct': 118.0,
          'valor_no_vencimento': 12680.0,
          'dias_para_vencimento': 361,
          'vencimento_proximo': false,
        },
        {
          'id': 2,
          'nome': 'LCI Inter',
          'tipo': 'lci',
          'valor_investido': 8000.0,
          'taxa': 96.0,
          'tipo_taxa': 'pos_fixado',
          'percentual_cdi': 96.0,
          'data_aplicacao': '2026-01-15',
          'vencimento': '2026-10-05',
          'liquidez': 'no_vencimento',
          'isento_ir': true,
          'oculto': false,
          'valor_atual': 8492.10,
          'rendimento_acumulado': 492.10,
          'rendimento_pct': 6.15,
          'meses_decorridos': 8,
          'taxa_anual_efetiva_pct': 10.7,
          'yield_equivalente_pct': 113.0,
          'valor_no_vencimento': 8610.0,
          'dias_para_vencimento': 20,
          'vencimento_proximo': true,
        },
      ],
      'total_investido': 18000.0,
      'total_atual': 19732.40,
      'total_rendimento': 1732.40,
      'rendimento_pct': 9.62,
      'taxa_media_aa': 12.8,
      'cdi_referencia': 11.15,
      'fonte_taxas': 'bcb',
    };
  }

  if (caminho.contains('/cashflow/month')) {
    return {
      ...base,
      'month': '2026-09',
      'received': 8400.0,
      'paid': 5210.40,
      'committed': 1180.00,
      'free_now': 2009.60,
      'surplus_low': 1109.60,
      'surplus_high': 1609.60,
      'has_range': true,
      'income_baseline': 8400.0,
      'estimate': {
        'base_months': ['2026-06', '2026-07', '2026-08'],
        'expected_low': 1800.0,
        'expected_high': 2300.0,
        'spent_so_far': 1400.0,
        'remaining_low': 400.0,
        'remaining_high': 900.0,
      },
      'due': [
        {
          'id': 11,
          'category': 'moradia',
          'description': 'Aluguel',
          'amount': 1800.0,
          'due_on': '2026-09-25',
        },
        {
          'id': 12,
          'category': 'contas_da_casa',
          'description': 'Luz',
          'amount': 180.0,
          'due_on': '2026-09-28',
        },
      ],
    };
  }

  if (caminho.contains('/cashflow/debts')) {
    return [
        {
          'id': 1,
          'kind': 'rotativo_cartao',
          'description': 'Fatura do cartão',
          'balance': 3200.0,
          'monthly_rate': 14.9,
          'class': 'expensive',
          'reference_monthly': 0.92,
          'reference_source': 'carteira',
          'flip_rate': 0.92,
        },
        {
          'id': 2,
          'kind': 'financiamento_veiculo',
          'description': 'Financiamento do carro',
          'balance': 21000.0,
          'monthly_rate': 0.84,
          'class': 'manageable',
          'reference_monthly': 0.92,
        'reference_source': 'carteira',
        'flip_rate': 0.92,
      },
    ];
  }

  if (caminho.contains('/surplus')) {
    return {
      ...base,
      'month': {
        'month': '2026-09',
        'received': 8400.0,
        'paid': 5210.40,
        'committed': 1180.00,
        'free_now': 2009.60,
        'surplus_low': 1109.60,
        'surplus_high': 1609.60,
        'has_range': true,
        'income_baseline': 8400.0,
        'estimate': {
          'base_months': ['2026-06', '2026-07', '2026-08'],
          'expected_low': 1800.0,
          'expected_high': 2300.0,
          'spent_so_far': 1400.0,
          'remaining_low': 400.0,
          'remaining_high': 900.0,
        },
        'due': <dynamic>[],
      },
      'has_cash': true,
      'cascade': {
        'surplus_low': 1109.60,
        'available_to_invest': 0.0,
        'steps': [
          {
            'order': 1,
            'type': 'debt',
            'amount': 1109.60,
            'reason': 'Fatura do cartão custa 14,90% ao mês. Sua carteira rendeu 0,92% ao mês. '
                'Enquanto essa diferença existir, quitar rende mais que aportar.',
            'falsifier': 'Se a taxa da dívida cair abaixo de 0,92% ao mês, quitar deixa de ser a '
                'prioridade.',
            'reference': 'carteira',
          },
        ],
      },
    };
  }

  if (caminho.contains('/rebalance-suggestions')) {
    return {
      ...base,
      'allocation_gaps': [
        {
          'category': 'renda_fixa',
          'current_pct': 18.5,
          'target_pct': 25.0,
          'gap_pct': 6.5,
          'gap_value': 6330.0,
        },
        {
          'category': 'acoes_br',
          'current_pct': 53.7,
          'target_pct': 45.0,
          'gap_pct': -8.7,
          'gap_value': -8470.0,
        },
      ],
      'items': [
        {
          'ticker': 'WEGE3',
          'name': 'WEG',
          'category': 'acoes_br',
          'verdict': 'SELL',
          'action': 'realocar',
          'current_value': 6178.80,
          'quantity': 120.0,
          'pnl_pct': 16.8,
          'reasons': [
            'Preço atual está 54% acima do teto da faixa de preço justo '
                '(R\$ 12,94 a R\$ 23,77).',
            'A categoria ações também está acima da meta de alocação.',
          ],
          'requires_tax_review': true,
          'label': 'Acima do preço justo',
          'margin_of_safety': -0.54,
          'adjustment_sentence': 'BBAS3 está 18% abaixo do preço justo e cabe na sua meta de '
              'renda, e você tem WEGE3, que está 54% acima — avalie se vale fazer o ajuste; o preço justo '
              'descreve posição, não antecipa retorno.',
          'realocar_para': {
            'ticker': 'BBAS3',
            'name': 'Banco do Brasil',
            'category': 'acoes_br',
            'score': 78.0,
            'verdict': 'STRONG_BUY',
            'label': 'Bem abaixo do preço justo',
            'price': 26.88,
            'fair_low': 32.80,
            'fair_high': 41.10,
            'margin_of_safety': 0.18,
            'fits_income_goal': true,
          },
        },
      ],
      'tax_disclaimer': 'Vender pode gerar imposto. O número do mês está na apuração.',
    };
  }

  if (caminho.contains('/opportunities')) {
    return {
      ...base,
      'items': [
        {
          'ticker': 'TAEE11',
          'name': 'Taesa',
          'sector': 'Energia',
          'price': 41.91,
          'fair_price': 103.17,
          'fair_low': 60.32,
          'fair_high': 146.03,
          'margin_of_safety': 0.3052,
          'dividend_yield': 8.64,
          'verdict': 'BUY',
          'label': 'Abaixo do preço justo',
          'basis': 'band',
          'band_quality': 'firme',
          'independent_inputs': 2,
          'confidence_label': 'alta',
          'score': 81.0,
          'confidence': 0.6,
          'data_years': 6,
          'trend_basis': 'long',
          'data_completeness': 1.0,
          'change_percent_day': 0.8,
          'distance_from_52w_high_pct': -12.4,
          'range_52w_position': 0.38,
        },
        {
          'ticker': 'BOVA11',
          'name': 'iShares Ibovespa',
          'sector': null,
          'price': 182.47,
          'fair_price': null,
          'fair_low': null,
          'fair_high': null,
          'margin_of_safety': null,
          'dividend_yield': 1.2,
          'verdict': 'UNKNOWN',
          'label': 'Sem preço justo',
          'basis': 'none',
          'band_quality': 'sem_faixa',
          'independent_inputs': 0,
          'confidence_label': 'baixa',
          'score': 0.0,
          'confidence': 0.0,
          'data_years': 0,
          'trend_basis': 'long',
          'data_completeness': 0.0,
          'change_percent_day': -0.4,
          'distance_from_52w_high_pct': -3.1,
          'range_52w_position': 0.72,
        },
      ],
      'total_count': 2,
      'universe_size': 412,
      'page': 1,
      'page_size': 30,
      'has_more': false,
    };
  }

  if (caminho.contains('/goals')) {
    return [
      {'category': 'acoes_br', 'target_pct': 45.0, 'target_value': 43843.0, 'declared': true},
      {'category': 'fiis', 'target_pct': 25.0, 'target_value': 24357.0, 'declared': true},
      {'category': 'renda_fixa', 'target_pct': 25.0, 'target_value': 24357.0, 'declared': true},
      {'category': 'etfs', 'target_pct': 5.0, 'target_value': 4871.0, 'declared': true},
    ];
  }

  if (caminho.contains('/sector-goals')) {
    return [
      {'sector': 'Energia', 'target_pct': 20.0, 'declared': true},
      {'sector': 'Bancos', 'target_pct': 15.0, 'declared': true},
    ];
  }

  if (caminho.contains('/alerts')) {
    return [
      {
        'id': 1,
        'ticker': 'PETR4',
        'condition': 'below',
        'target_price': 30.0,
        'note': 'Voltar a comprar',
      },
      {'id': 2, 'ticker': 'MXRF11', 'condition': 'above', 'target_price': 11.0},
    ];
  }

  if (caminho.contains('/referral')) {
    return {'code': 'MARIA2026', 'invited': 0, 'credited_until': null};
  }

  if (caminho.contains('/account/deletion-policy')) {
    return {
      'sla_days': 30,
      'removes': [
        'cash_entries',
        'debts',
        'dividends_received',
        'goals',
        'positions',
        'preferences',
        'price_alerts',
        'transactions',
      ],
      'note':
          'A remoção é imediata no banco de produção. O prazo declarado cobre backups e '
          'réplicas, onde o dado ainda pode existir até serem rotacionados. Nada disso está '
          'atrás de plano.',
      'confirmation_phrase': 'EXCLUIR',
    };
  }

  if (caminho.contains('/cashflow/entries')) {
    return [
        {
          'id': 1,
          'kind': 'income',
          'category': 'salario',
          'description': 'Salário',
          'amount': 8400.0,
          'due_on': '2026-09-05',
          'paid_on': '2026-09-05',
        },
        {
          'id': 2,
          'kind': 'expense',
          'category': 'moradia',
          'description': 'Aluguel',
          'amount': 1800.0,
          'due_on': '2026-09-25',
          'paid_on': null,
        },
        {
          'id': 3,
          'kind': 'expense',
          'category': 'mercado',
          'description': 'Compras do mês',
          'amount': 980.40,
        'due_on': '2026-09-08',
        'paid_on': '2026-09-08',
      },
    ];
  }

  if (caminho.contains('/transactions')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'kind': 'buy',
          'symbol': 'PETR4',
          'traded_on': '2026-08-14',
          'quantity': 200.0,
          'price': 38.42,
          'fees': 4.9,
        },
        {
          'id': 2,
          'kind': 'sell',
          'symbol': 'VALE3',
          'traded_on': '2026-07-30',
          'quantity': 50.0,
          'price': 61.10,
          'fees': 4.9,
        },
        {
          'id': 3,
          'kind': 'split',
          'symbol': 'WEGE3',
          'traded_on': '2026-06-12',
          'ratio_from': 1.0,
          'ratio_to': 2.0,
        },
      ],
      'count': 3,
    };
  }

  if (caminho.contains('/dividends/pending')) {
    return {
      'items': [
        {
          'ticker': 'BBAS3',
          'paid_at': '2026-09-05',
          'amount': 142.80,
          'quantity_at_date': 300.0,
          'rate_per_share': 0.476,
          'kind': 'jcp',
          'caveats': ['A quantidade usada é a de hoje, não a da data do crédito.'],
          'quantity_is_current': true,
        },
      ],
      'count': 1,
      'note': 'Sugestões do calendário cruzadas com a sua carteira.',
    };
  }

  if (caminho.contains('/dividends')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'ticker': 'PETR4',
          'paid_at': '2026-08-20',
          'amount': 318.40,
          'kind': 'dividendo',
        },
        {
          'id': 2,
          'ticker': 'MXRF11',
          'paid_at': '2026-08-15',
          'amount': 96.10,
          'kind': 'rendimento',
        },
      ],
      'total_received': 4820.50,
      'received_this_month': 414.50,
      'received_last_12m': 4120.00,
      'monthly_average_12m': 343.33,
      'total_count': 2,
      'by_ticker': [
        {'ticker': 'PETR4', 'total': 2480.0, 'count': 8},
        {'ticker': 'MXRF11', 'total': 1152.0, 'count': 12},
      ],
    };
  }

  return base;
}

const analiseDeAcao = {
  'symbol': 'ITSA4',
  'name': 'Itaúsa PN',
  'asset_type': 'br_stock',
  'sector': 'Financial Services',
  'price': 5.0,
  'as_of': 1790000000.0,
  'fair_price': {
    'fair_low': 6.55,
    'fair_high': 8.33,
    'principal_value': 7.41,
    'margin_of_safety': 0.2366,
    'band_quality': 'ampla',
    'independent_inputs': 2,
    'principal': 'lucros_descontados',
    'dy_12m': 0.1,
    'graham': 13.42,
    'personal_ceiling': 8.33,
    'data_years': 5,
    'methods': [
      {'method': 'dcf', 'input': 'lucro', 'role': 'principal', 'value': 7.41, 'status': 'ok', 'note': ''},
      {'method': 'bazin', 'input': 'dividendo', 'role': 'confirmacao', 'value': 5.22, 'status': 'ok', 'note': '', 'agreement': 'fora_ate_30'},
      {'method': 'vpa', 'input': 'patrimonio', 'role': 'inaplicavel', 'status': 'inaplicavel', 'note': 'vale para fundo imobiliário'},
      {'method': 'graham', 'input': 'lucro_e_patrimonio', 'role': 'indicador', 'value': 13.42, 'status': 'ok', 'note': ''},
    ],
    'premises': {
      'discount_rate': 0.145,
      'rate_base': 'selic_media_10a',
      'selic_pct': 9.5,
      'reference_date': '2026-09-23',
      'growth': 0.075,
      'long_run_growth': 0.045,
      'explicit_years': 5,
      'roe': 0.15,
      'payout': 0.5,
      'distributable': 0.5,
      'eps_normalized': 1.0,
      'earnings_years': 3,
      'value_without_growth': 7.11,
      'growth_creates_value': true,
      'breakeven_discount_rate': 0.1873,
    },
    'indicators': [
      {'kind': 'graham', 'value': 13.42, 'passes': true},
      {'kind': 'preco_teto_pessoal', 'value': 8.33, 'passes': true, 'desired_yield': 0.06},
      {'kind': 'pvp', 'value': 0.9, 'passes': null},
    ],
    'quality_reasons': ['a segunda conta fica fora da faixa, a até 30% dela'],
    'confirmation': {'method': 'bazin', 'value': 5.22, 'agreement': 'fora_ate_30'},
  },
  'technical': {'trend': 'uptrend', 'trend_basis': 'long', 'rsi_14': 74.0},
  'decision': {
    'verdict': 'BUY',
    'label': 'Abaixo do preço justo',
    'basis': 'band',
    'reasons': [
      'O preço está 23,7% abaixo do piso da faixa de preço justo, que vai de R\$ 6,55 a R\$ 8,33.',
      'Vale cerca de R\$ 7,41 pelo lucro que a empresa pode distribuir sem deixar de crescer.',
      'Uma segunda conta, pelos dividendos, dá R\$ 5,22, 20% abaixo do piso: não confirma a faixa.',
      'Qualidade da faixa: a segunda conta fica fora da faixa, a até 30% dela.',
      'Cabe na sua meta de renda: para render os 6% ao ano que você pediu em proventos, o '
          'preço-teto é R\$ 8,33, e o de hoje está abaixo.',
      'Na conta, a taxa exigida — o retorno mínimo para o investimento valer a pena — é de '
          '14,5% ao ano: a Selic média de 10 anos, o juro básico do país, mais 5 pontos. O lucro '
          'cresce 7,5% ao ano por 5 anos — o retorno sobre o patrimônio (ROE) de 15% vezes a '
          'parte do lucro que a empresa retém — e 4,5% depois. A faixa cobre esse cenário e o de '
          'não crescer e distribuir todo o lucro, com 1 ponto de taxa a mais e a menos.',
      'Preço sobre valor patrimonial (P/VP) de 0,90: paga-se menos que o patrimônio que está no '
          'balanço.',
      'O preço vem subindo: a média do preço nos últimos 50 dias está acima da média dos '
          'últimos 200. É contexto de preço, e não muda a leitura de valor.',
      'O preço subiu rápido em pouco tempo: o índice de força relativa (RSI) está em 74, de 0 a '
          '100. É contexto, não leitura de valor.',
    ],
    'falsifiers': [
      {'metric': 'price', 'condition': 'O preço cair para R\$ 4,58 ou menos', 'becomes_label': 'Bem abaixo do preço justo', 'current': 5.0, 'threshold': 4.585, 'kind': 'gatilho'},
      {'metric': 'price', 'condition': 'O preço subir para R\$ 5,57 ou mais', 'becomes_label': 'No preço justo', 'current': 5.0, 'threshold': 5.5675, 'kind': 'gatilho'},
      {
        'metric': 'discount_rate',
        'condition': 'A taxa exigida, o retorno mínimo que a conta pede ao ano, subir de 14,5% '
            'para 18,7%: aí o preço de hoje deixa de ter folga sobre o valor',
        'becomes_label': 'Rever a tese',
        'current': 0.145,
        'threshold': 0.1873,
        'kind': 'premissa',
      },
    ],
  },
};
