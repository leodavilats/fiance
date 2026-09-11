import 'package:flutter/material.dart';

import '../glossary.dart';
import '../theme.dart';

class HelpTooltip extends StatelessWidget {
  const HelpTooltip({
    super.key,
    required this.termKey,
    required this.label,
    this.child,
  });

  final String termKey;

  final String label;

  final Widget? child;

  @override
  Widget build(BuildContext context) {
    final text = glossary[termKey];
    final ink3 = fiInk3(context);

    final rotulo = Text(
      label,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: FiType.eyebrow.copyWith(color: ink3),
    );

    if (text == null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [rotulo, ?child],
      );
    }

    return Semantics(
      button: true,
      label: '$label. O que é isto? Abre a explicação do termo.',
      child: InkWell(
        borderRadius: BorderRadius.circular(FiRadius.sm),
        onTap: () => showModalBottomSheet<void>(
          context: context,
          showDragHandle: true,
          builder: (context) => SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                FiSpace.s5,
                0,
                FiSpace.s5,
                FiSpace.s6,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: FiType.title),
                  const SizedBox(height: FiSpace.s3),
                  Text(
                    text,
                    style: FiType.body.copyWith(color: fiInk2(context)),
                  ),
                ],
              ),
            ),
          ),
        ),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  border: Border(bottom: BorderSide(color: ink3)),
                ),
                child: rotulo,
              ),
              ?child,
            ],
          ),
        ),
      ),
    );
  }
}
