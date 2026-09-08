import 'package:flutter/material.dart';

import '../theme.dart';

/// Como conferir a conta de um julgamento renderizado: metodo, fonte, momento e limitacao.
///
/// No web e uma gaveta; aqui e um sheet, e o gatilho respeita `FiLayout.minTouchTarget`.
class FiProvenance extends StatelessWidget {
  const FiProvenance({
    super.key,
    this.summary = 'Como calculamos',
    this.method,
    this.source,
    this.asOf,
    this.limitation,
  });

  final String summary;
  final String? method;
  final String? source;

  /// Quando o dado foi coletado.
  final String? asOf;

  final String? limitation;

  bool get _temConteudo =>
      (method ?? source ?? asOf ?? limitation) != null;

  void _abrir(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(summary, style: FiType.title),
              const SizedBox(height: FiSpace.s4),
              _Campo(rotulo: 'Método', valor: method),
              _Campo(rotulo: 'Fonte', valor: source),
              _Campo(rotulo: 'Momento', valor: asOf),
              _Campo(rotulo: 'Limitação', valor: limitation),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!_temConteudo) return const SizedBox.shrink();

    return Semantics(
      button: true,
      label: '$summary. Abre método, fonte e limitações.',
      child: InkWell(
        onTap: () => _abrir(context),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
          child: Row(
            children: [
              Icon(Icons.info_outline, size: 14, color: fiInk3(context)),
              const SizedBox(width: FiSpace.s2),
              Expanded(
                child: Text(
                  summary,
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Campo extends StatelessWidget {
  const _Campo({required this.rotulo, required this.valor});

  final String rotulo;
  final String? valor;

  @override
  Widget build(BuildContext context) {
    final texto = valor;
    if (texto == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            rotulo,
            style: FiType.eyebrow.copyWith(color: fiInk3(context)),
          ),
          const SizedBox(height: FiSpace.s1),
          Text(texto, style: FiType.body.copyWith(color: fiInk2(context))),
        ],
      ),
    );
  }
}
