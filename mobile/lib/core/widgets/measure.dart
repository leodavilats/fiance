import 'package:flutter/material.dart';

import '../theme.dart';

/// A regua: um numero contra a distancia ate uma referencia.
///
/// E a forma geral -- score, saude, progresso de meta, desvio de alocacao, margem de seguranca.
/// `ScoreRuler` e a variante de **score**, com as bandas do sistema.
class FiMeasure extends StatelessWidget {
  const FiMeasure({
    super.key,
    required this.label,
    required this.value,
    this.min = 0,
    this.max = 100,
    this.reference,
    this.readout,
    this.note,
    this.state = FiState.neutral,
    this.fillColor,
    this.semantics,
  });

  final String label;
  final double value;
  final double min;
  final double max;

  /// O alvo, desenhado como marca vertical sobre o trilho. Sem referencia a regua so mede.
  final double? reference;

  /// O numero como a pessoa o le -- ja formatado, com unidade.
  final String? readout;

  /// A leitura em palavras: a banda, o que falta, o que a derrubaria.
  final String? note;

  /// O julgamento sobre o valor. Decide a tinta da leitura.
  final FiState state;

  /// A tinta do preenchimento quando ela carrega identidade propria. Estado continua mandando
  /// na leitura escrita.
  final Color? fillColor;

  final String? semantics;

  double get _fracao {
    final span = max - min;
    if (span <= 0) return 0;
    return ((value - min) / span).clamp(0.0, 1.0);
  }

  double? get _refFracao {
    final r = reference;
    if (r == null) return null;
    final span = max - min;
    if (span <= 0) return null;
    return ((r - min) / span).clamp(0.0, 1.0);
  }

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink1 = fiInk1Of(brightness);
    final ink3 = fiInk3Of(brightness);
    final corDoEstado = fiStateColor(state, brightness);
    final preenchimento = fillColor ?? corDoEstado;

    return Semantics(
      label: semantics ?? '$label: ${readout ?? value.toStringAsFixed(0)}'
          '${note == null ? '' : ' — $note'}',
      child: ExcludeSemantics(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: FiSpace.s2),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Expanded(
                    child: Text(label, style: FiType.body.copyWith(color: ink1)),
                  ),
                  if (readout != null)
                    Flexible(
                      child: Text(
                        readout!,
                        textAlign: TextAlign.end,
                        style: FiType.figure.copyWith(color: ink1),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: FiSpace.s2),
              LayoutBuilder(
                builder: (context, constraints) {
                  final largura = constraints.maxWidth;
                  final marca = _refFracao;
                  return SizedBox(
                    height: 10,
                    child: Stack(
                      children: [
                        Positioned(
                          left: 0,
                          right: 0,
                          top: 1,
                          height: 8,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: fiGround2(brightness),
                              borderRadius: BorderRadius.circular(FiRadius.sm),
                            ),
                          ),
                        ),
                        Positioned(
                          left: 0,
                          width: largura * _fracao,
                          top: 1,
                          height: 8,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: preenchimento,
                              borderRadius: BorderRadius.circular(FiRadius.sm),
                            ),
                          ),
                        ),
                        if (marca != null)
                          Positioned(
                            left: (largura * marca - 1).clamp(0.0, largura - 2),
                            top: 0,
                            bottom: 0,
                            width: 2,
                            child: ColoredBox(color: ink1),
                          ),
                      ],
                    ),
                  );
                },
              ),
              if (note != null) ...[
                const SizedBox(height: FiSpace.s1),
                Text(
                  note!,
                  style: FiType.caption.copyWith(
                    color: state == FiState.neutral ? ink3 : corDoEstado,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
