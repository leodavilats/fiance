import 'package:flutter/material.dart';

import '../theme.dart';

class FiSection extends StatelessWidget {
  const FiSection({
    super.key,
    required this.title,
    this.count,
    this.hint,
    this.trailing,
    this.action,
    required this.child,
    this.first = false,
  });

  final String title;

  final int? count;

  final String? hint;

  final Widget? trailing;

  final Widget? action;

  final Widget child;

  final bool first;

  @override
  Widget build(BuildContext context) {
    final cabecalho = count == null ? title : '$title · $count';

    return Padding(
      padding: EdgeInsets.only(top: first ? FiSpace.s2 : FiSpace.s8),
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
            const SizedBox(height: FiSpace.s2),
            Text(
              hint!,
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
          ],
          const SizedBox(height: FiSpace.s3),
          child,
          if (action != null) ...[
            const SizedBox(height: FiSpace.s2),
            Align(alignment: Alignment.centerLeft, child: action!),
          ],
        ],
      ),
    );
  }
}

class FiFigures extends StatelessWidget {
  const FiFigures({super.key, required this.figures, this.rule = true});

  final Map<String, String> figures;

  final bool rule;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (rule) ...[
          Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
          const SizedBox(height: FiSpace.s3),
        ],
        Wrap(
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
        ),
      ],
    );
  }
}

class FiHeadline extends StatelessWidget {
  const FiHeadline({
    super.key,
    required this.eyebrow,
    required this.figure,
    this.size = FiHeadlineSize.lg,
    this.support,
    this.supportColor,
    this.note,
  });

  final String eyebrow;
  final String figure;
  final FiHeadlineSize size;

  final String? support;

  final Color? supportColor;

  final String? note;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          eyebrow.toUpperCase(),
          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
        ),
        const SizedBox(height: FiSpace.s1),
        Text(
          figure,
          style: (size == FiHeadlineSize.xl ? FiType.moneyXl : FiType.moneyLg)
              .copyWith(color: fiInk1(context)),
        ),
        if (support != null) ...[
          const SizedBox(height: FiSpace.s2),
          Text(
            support!,
            style: FiType.body.copyWith(color: supportColor ?? fiInk2(context)),
          ),
        ],
        if (note != null) ...[
          const SizedBox(height: FiSpace.s1),
          Text(note!, style: FiType.caption.copyWith(color: fiInk3(context))),
        ],
      ],
    );
  }
}

enum FiHeadlineSize { lg, xl }
