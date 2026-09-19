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
  late final PageController _control = PageController(
    initialPage: widget.navigationShell.currentIndex,
  );

  @override
  void didUpdateWidget(FiBranchPager oldWidget) {
    super.didUpdateWidget(oldWidget);
    final destino = widget.navigationShell.currentIndex;
    if (!_control.hasClients) return;

    final current = _control.page?.round();
    if (current == destino) return;

    if (current == null || (current - destino).abs() > 1) {
      _control.jumpToPage(destino);
      return;
    }

    _control.animateToPage(
      destino,
      duration: FiMotion.base,
      curve: FiMotion.easeEnter,
    );
  }

  @override
  void dispose() {
    _control.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PageView(
      controller: _control,
      onPageChanged: (indice) {
        if (indice == widget.navigationShell.currentIndex) return;
        widget.navigationShell.goBranch(indice);
      },
      children: [for (final ramo in widget.children) _KeepAlive(child: ramo)],
    );
  }
}

class _KeepAlive extends StatefulWidget {
  const _KeepAlive({required this.child});

  final Widget child;

  @override
  State<_KeepAlive> createState() => _KeepAliveState();
}

class _KeepAliveState extends State<_KeepAlive> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return widget.child;
  }
}
