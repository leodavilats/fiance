import 'package:flutter/material.dart';

import '../theme.dart';

/// Uma secao: fio e chao, nao card.
///
/// `Semantics(header: true)` da a quem usa leitor de tela a navegacao por cabecalho que o `<h2>`
/// da no web. `Card` fica reservado ao que e objeto.
class FiSection extends StatelessWidget {
  const FiSection({
    super.key,
    required this.title,
    this.count,
    this.hint,
    this.trailing,
    required this.child,
    this.first = false,
  });

  final String title;

  /// Sufixo `· N`, para titulo que carrega quantidade.
  final int? count;

  final String? hint;

  final Widget? trailing;

  final Widget child;

  /// A primeira secao nao desenha o fio de cima.
  final bool first;

  @override
  Widget build(BuildContext context) {
    final cabecalho = count == null ? title : '$title · $count';

    return Padding(
      padding: EdgeInsets.only(top: first ? FiSpace.s2 : FiSpace.s6),
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
            const SizedBox(height: FiSpace.s1),
            Text(
              hint!,
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
          ],
          const SizedBox(height: FiSpace.s3),
          child,
        ],
      ),
    );
  }
}

/// Cifras rotuladas sob um fio, no lugar de uma grade de KPI.
class FiFigures extends StatelessWidget {
  const FiFigures({super.key, required this.figures});

  /// Rotulo -> valor ja formatado, na ordem da leitura.
  final Map<String, String> figures;

  @override
  Widget build(BuildContext context) {
    return Wrap(
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
    );
  }
}
