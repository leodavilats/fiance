import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../theme.dart';

class FiActionScaffold extends StatefulWidget {
  const FiActionScaffold({super.key, this.appBar, required this.body, this.action});

  final PreferredSizeWidget? appBar;
  final Widget body;
  final Widget? action;

  @override
  State<FiActionScaffold> createState() => _FiActionScaffoldState();
}

class _FiActionScaffoldState extends State<FiActionScaffold> {
  bool _visivel = true;

  void _mostrar(bool visivel) {
    if (visivel != _visivel) setState(() => _visivel = visivel);
  }

  bool _aoRolar(ScrollNotification n) {
    if (n.depth != 0) return false;
    if (n is UserScrollNotification) {
      if (n.direction == ScrollDirection.reverse) _mostrar(false);
      if (n.direction == ScrollDirection.forward) _mostrar(true);
    }
    if (n is ScrollEndNotification && n.metrics.extentAfter == 0) _mostrar(true);
    return false;
  }

  @override
  Widget build(BuildContext context) {
    final acao = widget.action;

    return Scaffold(
      appBar: widget.appBar,
      floatingActionButton: acao == null
          ? null
          : AnimatedSlide(
              offset: _visivel ? Offset.zero : const Offset(0, 2),
              duration: FiMotion.base,
              curve: _visivel ? FiMotion.easeEnter : FiMotion.easeExit,
              child: acao,
            ),
      body: NotificationListener<ScrollNotification>(
        onNotification: _aoRolar,
        child: widget.body,
      ),
    );
  }
}
