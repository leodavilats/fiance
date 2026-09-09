import 'package:flutter/material.dart';

import '../design_tokens.dart';

/// A forma do que está chegando, e não um disco girando no meio da tela.
///
/// Os papéis são os mesmos de `<app-skeleton>` no web: a altura de cada um é a do papel de
/// tipografia que vai ocupar aquele lugar, para a página não saltar quando o dado chega.
enum FiSkeletonShape { moneyXl, verdict, metric, title, body, caption, ruler, row }

class FiSkeleton extends StatefulWidget {
  const FiSkeleton({super.key, this.shape = FiSkeletonShape.body, this.count = 1});

  final FiSkeletonShape shape;
  final int count;

  /// O esqueleto de uma tela inteira, com a margem que uma lista usaria.
  static Widget tela({
    FiSkeletonShape shape = FiSkeletonShape.row,
    int count = 5,
    String label = 'Carregando estas informações',
  }) {
    return Semantics(
      label: label,
      liveRegion: true,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(FiSpace.s4, FiSpace.s4, FiSpace.s4, FiSpace.s8),
        children: [FiSkeleton(shape: shape, count: count)],
      ),
    );
  }

  @override
  State<FiSkeleton> createState() => _FiSkeletonState();
}

class _FiSkeletonState extends State<FiSkeleton> with SingleTickerProviderStateMixin {
  late final AnimationController _pulso = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1400),
  );

  @override
  void initState() {
    super.initState();
    _pulso.repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulso.dispose();
    super.dispose();
  }

  double get _altura => switch (widget.shape) {
    FiSkeletonShape.moneyXl => 40,
    FiSkeletonShape.verdict => 26,
    FiSkeletonShape.metric => 26,
    FiSkeletonShape.title => 20,
    FiSkeletonShape.ruler => 8,
    FiSkeletonShape.row => 16,
    FiSkeletonShape.caption => 12,
    FiSkeletonShape.body => 14,
  };

  List<double> get _larguras {
    const base = <FiSkeletonShape, List<double>>{
      FiSkeletonShape.moneyXl: [0.58],
      FiSkeletonShape.verdict: [0.82, 0.64],
      FiSkeletonShape.metric: [0.40],
      FiSkeletonShape.title: [0.46],
      FiSkeletonShape.body: [1.0, 0.88, 0.72],
      FiSkeletonShape.caption: [0.38],
      FiSkeletonShape.ruler: [1.0],
      FiSkeletonShape.row: [1.0],
    };

    final padrao = base[widget.shape]!;
    if (widget.shape == FiSkeletonShape.row) {
      return List<double>.filled(widget.count, 1.0);
    }
    if (widget.count <= 1) return padrao;
    return List<double>.generate(widget.count, (i) => padrao[i % padrao.length]);
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final tinta = isDark ? FiColors.darkInk3 : FiColors.lightInk3;
    final espaco = widget.shape == FiSkeletonShape.row ? FiSpace.s5 : FiSpace.s2;
    final larguras = _larguras;

    return ExcludeSemantics(
      child: AnimatedBuilder(
        animation: _pulso,
        builder: (context, _) {
          // `disableAnimations` é a preferência do sistema por menos movimento: o pulso some,
          // a forma fica.
          final reduzido = MediaQuery.maybeDisableAnimationsOf(context) ?? false;
          final opacidade = reduzido ? 0.30 : 0.30 * (1 - 0.45 * _pulso.value);

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < larguras.length; i++)
                Padding(
                  padding: EdgeInsets.only(top: i == 0 ? 0 : espaco),
                  child: FractionallySizedBox(
                    alignment: Alignment.centerLeft,
                    widthFactor: larguras[i],
                    child: Container(
                      height: _altura,
                      decoration: BoxDecoration(
                        color: tinta.withValues(alpha: opacidade),
                        borderRadius: BorderRadius.circular(FiRadius.sm),
                      ),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
