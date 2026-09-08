import 'package:flutter/material.dart';

import '../theme.dart';

/// Uma secao: fio e chao, nao card.
///
/// Equivalente do `<app-section>` do web, e com a mesma razao de existir: a secao precisa emitir
/// um **cabecalho**, e classe (ou convencao) nao obriga nada. `Semantics(header: true)` e o que
/// da a quem usa leitor de tela a mesma navegacao por cabecalho que o `<h2>` da no web.
///
/// A caixa (`Card`) fica reservada ao que e **objeto** -- uma posicao, um titulo, uma sugestao.
/// Secao e espaco, tipo e uma regra horizontal.
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

  /// Sufixo `· N`, para secao cujo titulo carrega quantidade ("A vencer · 3").
  final int? count;

  final String? hint;

  /// Acao a direita do titulo -- o equivalente do slot `sectionActions`.
  final Widget? trailing;

  final Widget child;

  /// A primeira secao da tela nao desenha o fio de cima: ele separaria do titulo da tela.
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

/// Uma cifra rotulada, sob um fio -- a alternativa a grade de KPI.
///
/// Tres a quatro caixas centralizadas com um numero dentro nao sao informacao organizada, sao
/// widgets. Aqui as cifras dividem uma linha e o rotulo fica em cima, no papel de legenda.
class FiFigures extends StatelessWidget {
  const FiFigures({super.key, required this.figures});

  /// Rotulo -> valor ja formatado. A ordem e a da leitura, nao a do modelo.
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
