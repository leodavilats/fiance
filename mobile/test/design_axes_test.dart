import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/design_tokens.dart';
import 'package:fiance/core/labels.dart';

/// Os dois eixos de cor do sistema não podem voltar a se misturar.
///
/// `gainColor`/`lossColor`/`warnColor` existiam e faziam os dois papéis ao
/// mesmo tempo: P&L (aritmética) e veredito (julgamento) saíam da mesma função,
/// com a mesma saturação. Estes testes travam a separação e a identidade de
/// série compartilhada com o web.
void main() {
  group('estado × direção', () {
    test('direção tem croma mais baixo que estado', () {
      final favorable = HSLColor.fromColor(
        fiStateColor(FiState.favorable, Brightness.dark),
      );
      final up = HSLColor.fromColor(fiDirectionColor(1, Brightness.dark));

      expect(up.saturation, lessThan(favorable.saturation));
    });

    test('direção zero não é nem alta nem baixa', () {
      expect(
        fiDirectionColor(0, Brightness.dark),
        equals(FiColors.darkInk2),
      );
    });

    test('estado indeterminado existe e é distinto de adverso', () {
      expect(
        fiStateColor(FiState.indeterminate, Brightness.dark),
        isNot(equals(fiStateColor(FiState.adverse, Brightness.dark))),
      );
    });
  });

  group('identidade de série', () {
    test('categoria e tipo de ativo compartilham a mesma cor', () {
      expect(
        categoryColor('fiis', Brightness.dark),
        equals(fiSeriesColor(3, Brightness.dark)),
      );
    });

    test('categoria desconhecida cai em "outros", não numa cor sorteada', () {
      expect(
        categoryColor('cripto', Brightness.dark),
        equals(FiColors.darkSeriesOther),
      );
    });

    test('setor tem cor estável e igual à do web', () {
      expect(
        sectorColor('Financeiro', Brightness.light),
        equals(FiColors.lightSeries1),
      );
      expect(
        sectorColor('Telecomunicações', Brightness.light),
        equals(FiColors.lightSeries11),
      );
    });
  });

  group('régua de desvio de alocação', () {
    test('desvio nunca é julgado como adverso — só como atenção', () {
      for (final band in fiAllocationGapBands) {
        expect(band.state, isNot(FiState.adverse));
      }
    });

    test('dentro da tolerância a leitura é "na meta"', () {
      expect(fiBandFor(0.5, fiAllocationGapBands, 1).id, 'on-target');
      expect(fiBandFor(3, fiAllocationGapBands, 1).id, 'drift');
      expect(fiBandFor(9, fiAllocationGapBands, 1).id, 'relevant');
    });

    test('sem meta o estado é indeterminado, não zero', () {
      final band = fiBandFor(0, fiAllocationGapBands, 0);
      expect(band.state, FiState.indeterminate);
      expect(band.min, isNull);
    });
  });
}
