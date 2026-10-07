import 'package:flutter/material.dart';

import '../theme.dart';
import 'help_tooltip.dart';

class FiDataRow extends StatelessWidget {
  const FiDataRow({
    super.key,
    required this.label,
    this.value,
    this.valueColor,
    this.detail,
    this.note,
    this.leading,
    this.trailing,
    this.onTap,
    this.emphasis = false,
    this.dense = false,
    this.glossaryKey,
    this.chevron = true,
  });

  final String? glossaryKey;

  final bool chevron;

  final String label;

  final String? value;

  final Color? valueColor;

  final String? detail;

  final Widget? trailing;

  final Widget? leading;

  final String? note;

  final bool emphasis;

  final bool dense;

  final VoidCallback? onTap;

  String get _spoken => [
    value == null ? label : '$label: $value',
    ?detail,
    ?note,
  ].join('. ');

  @override
  Widget build(BuildContext context) {
    final navegavel = onTap != null;
    final explicavel = !navegavel && hasGlossaryEntry(glossaryKey);
    final falado = navegavel || explicavel;
    final estiloDoRotulo = emphasis
        ? FiType.title
        : FiType.body.copyWith(color: fiInk1(context));

    final corpo = Padding(
      padding: EdgeInsets.symmetric(vertical: dense ? FiSpace.s2 : FiSpace.s3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (leading != null) ...[
            leading!,
            const SizedBox(width: FiSpace.s3),
          ],
          Expanded(
            child: ExcludeSemantics(
              excluding: falado,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: explicavel
                        ? estiloDoRotulo.copyWith(
                            decoration: TextDecoration.underline,
                            decorationStyle: TextDecorationStyle.dotted,
                            decorationColor: fiInk3(context),
                          )
                        : estiloDoRotulo,
                  ),
                  if (detail != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      detail!,
                      style: FiType.caption.copyWith(color: fiInk2(context)),
                    ),
                  ],
                  if (note != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      note!,
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (value != null || trailing != null) const SizedBox(width: FiSpace.s4),
          if (value != null)
            Flexible(
              fit: FlexFit.tight,
              child: Align(
                alignment: Alignment.centerRight,
                child: ExcludeSemantics(
                  excluding: falado,
                  child: Text(
                    value!,
                    textAlign: TextAlign.end,
                    style: (emphasis ? FiType.metricSm : FiType.figure).copyWith(
                      color: valueColor ?? fiInk1(context),
                    ),
                  ),
                ),
              ),
            ),
          ?trailing,
          if (navegavel && chevron) ...[
            const SizedBox(width: FiSpace.s2),
            Icon(Icons.chevron_right, size: 18, color: fiInk3(context)),
          ],
        ],
      ),
    );

    if (explicavel) {
      return Semantics(
        button: true,
        label: glossarySemantics(_spoken),
        child: InkWell(
          onTap: () => showGlossaryTerm(context, glossaryKey!, label),
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
            child: corpo,
          ),
        ),
      );
    }

    if (!navegavel) return corpo;

    return Semantics(
      button: true,
      label: _spoken,
      child: InkWell(
        onTap: onTap,
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
          child: corpo,
        ),
      ),
    );
  }
}

class FiRows extends StatelessWidget {
  const FiRows({super.key, required this.children, this.divided = true});

  final List<Widget> children;

  final bool divided;

  @override
  Widget build(BuildContext context) {
    if (children.isEmpty) return const SizedBox.shrink();
    if (!divided) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: children);
    }

    final hairline = fiHairline(Theme.of(context).brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < children.length; i++) ...[
          if (i > 0) Divider(color: hairline, height: 1, thickness: 1),
          children[i],
        ],
      ],
    );
  }
}

class FiObject extends StatelessWidget {
  const FiObject({
    super.key,
    required this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(FiSpace.s4),
    this.accent,
    this.semanticsLabel,
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsets padding;

  final Color? accent;

  final String? semanticsLabel;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final borda = fiHairline(brightness);

    final conteudo = Padding(padding: padding, child: child);

    final inner = accent == null
        ? conteudo
        : IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(width: 3, color: accent),
                Expanded(child: conteudo),
              ],
            ),
          );

    Widget corpo = Material(
      color: fiGround1(brightness),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(FiRadius.md),
        side: BorderSide(color: borda),
      ),
      clipBehavior: Clip.antiAlias,
      child: onTap == null ? inner : InkWell(onTap: onTap, child: inner),
    );

    if (semanticsLabel != null) {
      corpo = Semantics(label: semanticsLabel, container: true, child: corpo);
    }

    return corpo;
  }
}
