import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';

class FiBranchPager extends StatefulWidget {
  const FiBranchPager({
    super.key,
    required this.navigationShell,
    required this.children,
  });

  final StatefulNavigationShell navigationShell;
  final List<Widget> children;

  @override
  State<FiBranchPager> createState() => _FiBranchPagerState();
}

class _FiBranchPagerState extends State<FiBranchPager> {
  late final PageController _controle = PageController(
    initialPage: widget.navigationShell.currentIndex,
  );

  @override
  void didUpdateWidget(FiBranchPager oldWidget) {
    super.didUpdateWidget(oldWidget);
    final destino = widget.navigationShell.currentIndex;
    if (!_controle.hasClients) return;

    final atual = _controle.page?.round();
    if (atual == destino) return;

    if (atual == null || (atual - destino).abs() > 1) {
      _controle.jumpToPage(destino);
      return;
    }

    _controle.animateToPage(
      destino,
      duration: FiMotion.base,
      curve: FiMotion.easeEnter,
    );
  }

  @override
  void dispose() {
    _controle.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PageView(
      controller: _controle,
      onPageChanged: (indice) {
        if (indice == widget.navigationShell.currentIndex) return;
        widget.navigationShell.goBranch(indice);
      },
      children: [for (final ramo in widget.children) _Vivo(child: ramo)],
    );
  }
}

class _Vivo extends StatefulWidget {
  const _Vivo({required this.child});

  final Widget child;

  @override
  State<_Vivo> createState() => _VivoState();
}

class _VivoState extends State<_Vivo> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return widget.child;
  }
}
