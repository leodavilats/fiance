import 'package:flutter/material.dart';

import '../theme.dart';

/// Uma secao: fio e chao, nao card.
///
/// `Semantics(header: true)` da a quem usa leitor de tela a navegacao por cabecalho que o `<h2>`
/// da no web. A caixa fica reservada ao que e objeto, e isso e `FiObject`.
class FiSection extends StatelessWidget {
  const FiSection({
    super.key,
    required this.title,
    this.count,
    this.hint,
    this.trailing,
    this.action,
    required this.child,
    this.first = false,
  });

  final String title;

  /// Sufixo `· N`, para titulo que carrega quantidade.
  final int? count;

  final String? hint;

  /// O recorte do que vem abaixo: muda o que se le, e por isso fica no cabecalho.
  final Widget? trailing;

  /// A acao que a secao habilita: vem **depois** do conteudo, nunca ao lado do titulo.
  final Widget? action;

  final Widget child;

  /// A primeira secao nao desenha o fio de cima.
  final bool first;

  @override
  Widget build(BuildContext context) {
    final cabecalho = count == null ? title : '$title · $count';

    return Padding(
      padding: EdgeInsets.only(top: first ? FiSpace.s2 : FiSpace.s8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!first) ...[
            Divider(
              color: Theme.of(context).dividerColor,
              height: 1,
              thickness: 1,
            ),
            const SizedBox(height: FiSpace.s5),
          ],
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Expanded(
                child: Semantics(
                  header: true,
                  child: Text(
                    cabecalho,
                    style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                  ),
                ),
              ),
              ?trailing,
            ],
          ),
          if (hint != null) ...[
            const SizedBox(height: FiSpace.s2),
            Text(
              hint!,
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
          ],
          const SizedBox(height: FiSpace.s3),
          child,
          if (action != null) ...[
            const SizedBox(height: FiSpace.s2),
            Align(alignment: Alignment.centerLeft, child: action!),
          ],
        ],
      ),
    );
  }
}

/// Cifras rotuladas sob um fio, no lugar de uma grade de KPI.
class FiFigures extends StatelessWidget {
  const FiFigures({super.key, required this.figures, this.rule = true});

  /// Rotulo -> valor ja formatado, na ordem da leitura.
  final Map<String, String> figures;

  /// O fio sobre a linha de cifras. Sai quando ja ha um logo acima.
  final bool rule;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (rule) ...[
          Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
          const SizedBox(height: FiSpace.s3),
        ],
        Wrap(
          spacing: FiSpace.s8,
          runSpacing: FiSpace.s4,
          children: [
            for (final e in figures.entries)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    e.key,
                    style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                  ),
                  const SizedBox(height: FiSpace.s1),
                  Text(e.value, style: FiType.metricSm),
                ],
              ),
          ],
        ),
      ],
    );
  }
}

class FiHeadline extends StatelessWidget {
  const FiHeadline({
    super.key,
    required this.eyebrow,
    required this.figure,
    this.size = FiHeadlineSize.lg,
    this.support,
    this.supportColor,
    this.note,
  });

  final String eyebrow;
  final String figure;
  final FiHeadlineSize size;

  final String? support;

  /// A tinta da leitura, quando ela é direção. Julgamento não passa por aqui: veredito é bloco
  /// próprio, em serifa.
  final Color? supportColor;

  final String? note;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          eyebrow.toUpperCase(),
          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
        ),
        const SizedBox(height: FiSpace.s1),
        Text(
          figure,
          style: (size == FiHeadlineSize.xl ? FiType.moneyXl : FiType.moneyLg)
              .copyWith(color: fiInk1(context)),
        ),
        if (support != null) ...[
          const SizedBox(height: FiSpace.s2),
          Text(
            support!,
            style: FiType.body.copyWith(color: supportColor ?? fiInk2(context)),
          ),
        ],
        if (note != null) ...[
          const SizedBox(height: FiSpace.s1),
          Text(note!, style: FiType.caption.copyWith(color: fiInk3(context))),
        ],
      ],
    );
  }
}

/// `xl` é para a tela cujo assunto **é** aquele número; `lg`, para a que abre por ele e discute
/// outra coisa.
enum FiHeadlineSize { lg, xl }
