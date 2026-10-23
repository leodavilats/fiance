import 'package:flutter/material.dart';

import '../theme.dart';

class FiShortcut {
  const FiShortcut({
    required this.label,
    required this.icon,
    required this.onTap,
    this.detail,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;
  final String? detail;
}

class FiShortcuts extends StatelessWidget {
  const FiShortcuts({super.key, required this.items, this.columns = 2});

  final List<FiShortcut> items;

  final int columns;

  @override
  Widget build(BuildContext context) {
    final fio = fiHairline(Theme.of(context).brightness);
    final linhas = [
      for (var i = 0; i < items.length; i += columns)
        items.sublist(i, (i + columns).clamp(0, items.length)),
    ];

    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.symmetric(horizontal: BorderSide(color: fio)),
      ),
      child: Column(
        children: [
          for (var l = 0; l < linhas.length; l++) ...[
            if (l > 0) Divider(color: fio, height: 1, thickness: 1),
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (var c = 0; c < columns; c++) ...[
                    if (c > 0) VerticalDivider(color: fio, width: 1, thickness: 1),
                    Expanded(
                      child: c < linhas[l].length
                          ? _Tile(item: linhas[l][c], first: c == 0, last: c == columns - 1)
                          : const SizedBox.shrink(),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  const _Tile({required this.item, required this.first, required this.last});

  final FiShortcut item;
  final bool first;
  final bool last;

  @override
  Widget build(BuildContext context) {
    final marca = Theme.of(context).colorScheme.primary;
    final detalhe = item.detail;

    return Semantics(
      button: true,
      label: detalhe == null ? item.label : '${item.label}. $detalhe',
      onTap: item.onTap,
      child: ExcludeSemantics(
        child: InkWell(
          onTap: item.onTap,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
            child: Padding(
              padding: EdgeInsets.fromLTRB(
                first ? 0 : FiSpace.s3,
                FiSpace.s3,
                last ? 0 : FiSpace.s3,
                FiSpace.s3,
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(item.icon, size: 20, color: marca),
                  const SizedBox(width: FiSpace.s2),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(item.label, style: FiType.label.copyWith(color: fiInk1(context))),
                        if (detalhe != null) ...[
                          const SizedBox(height: 2),
                          Text(
                            detalhe,
                            style: FiType.caption.copyWith(color: fiInk3(context)),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
