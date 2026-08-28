import 'package:fiance/core/models.dart';
import 'package:fiance/features/busca/busca_screen.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('dobramento de acento', () {
    test('"tesouro selic" acha "Tesouro Selic"', () {
      // Em português isso não é refinamento: é o caso comum, e casar só o
      // exato faria a busca parecer quebrada com os nomes mais frequentes.
      expect(dobrar('Tesouro Selic'), 'tesouro selic');
      expect(dobrar('AÇÃO'), 'acao');
      expect(dobrar('Projeção'), 'projecao');
    });

    test('texto sem acento passa intacto', () {
      expect(dobrar('CDB'), 'cdb');
    });
  });

  group('destinos vivem no cliente', () {
    test('consulta vazia não devolve o catálogo inteiro', () {
      // Uma caixa que despeja o produto ao ganhar foco ensina a pessoa a
      // fechá-la.
      expect(destinosPara(''), isEmpty);
      expect(destinosPara('   '), isEmpty);
    });

    test('o vocabulário é o de quem procura, não o do código', () {
      // "Provento" e "dividendo" são a mesma pergunta.
      final porProvento = destinosPara('provento').map((d) => d.route);
      final porDividendo = destinosPara('dividendo').map((d) => d.route);

      expect(porProvento, contains('/carteira'));
      expect(porDividendo, contains('/carteira'));
    });

    test('acha metas pelo nome da tela', () {
      expect(
        destinosPara('metas').map((d) => d.route),
        contains('/estrategia/metas'),
      );
    });

    test('acha a atividade por "histórico", com acento', () {
      expect(
        destinosPara('histórico').map((d) => d.route),
        contains('/hoje/atividade'),
      );
    });

    test('a lista tem teto: busca é atalho, não listagem', () {
      expect(destinosPara('a').length, lessThanOrEqualTo(5));
    });

    test('toda rota de destino começa com barra', () {
      // Rota relativa no `go_router` navega para o lugar errado dependendo de
      // onde a pessoa estiver quando buscar.
      for (final destino in buscaDestinos) {
        expect(destino.route.startsWith('/'), isTrue, reason: destino.title);
      }
    });
  });

  group('a rota do achado é decidida no cliente', () {
    SearchHit hit(String kind, String ref) =>
        SearchHit(kind: kind, title: ref, subtitle: '', ref: ref);

    test('posição leva à página do ativo', () {
      expect(rotaDoAchado(hit('position', 'PETR4')), '/ativo/PETR4');
    });

    test('ativo do universo também', () {
      expect(rotaDoAchado(hit('asset', 'VALE3')), '/ativo/VALE3');
    });

    test(
      'renda fixa leva à tela de renda fixa, não a um ativo inexistente',
      () {
        // O `ref` da renda fixa é um id numérico: montar `/ativo/7` daria 404.
        expect(rotaDoAchado(hit('fixed_income', '7')), '/carteira/renda-fixa');
      },
    );
  });

  group('leitura da resposta', () {
    test('grupos e itens chegam na ordem que o servidor mandou', () {
      final r = SearchResults.fromJson({
        'query': 'petr',
        'groups': [
          {
            'label': 'Na sua carteira',
            'items': [
              {
                'kind': 'position',
                'title': 'PETR4',
                'subtitle': '100 na carteira',
                'ref': 'PETR4',
              },
            ],
          },
          {
            'label': 'Ativos',
            'items': [
              {
                'kind': 'asset',
                'title': 'PETR3',
                'subtitle': 'Petrobras',
                'ref': 'PETR3',
              },
            ],
          },
        ],
        'total': 2,
      });

      expect(r.groups.first.label, 'Na sua carteira');
      expect(r.total, 2);
    });

    test('resposta sem grupos não estoura', () {
      final r = SearchResults.fromJson({'query': 'zzz', 'total': 0});

      expect(r.groups, isEmpty);
      expect(r.total, 0);
    });
  });
}
