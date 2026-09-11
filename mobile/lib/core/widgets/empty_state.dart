import 'package:flutter/material.dart';

import '../theme.dart';
import 'button.dart';

class FiEmptyState extends StatelessWidget {
  const FiEmptyState({
    super.key,
    required this.title,
    required this.body,
    this.hint,
    this.action,
    this.secondary,
  });

  final String title;

  final String body;

  final String? hint;

  final Widget? action;
  final Widget? secondary;

  @override
  Widget build(BuildContext context) {
    final acao = action;

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s8,
        FiLayout.gutter,
        FiSpace.s6,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: fiSerif(FiType.verdict).copyWith(color: fiInk1(context)),
          ),
          const SizedBox(height: FiSpace.s3),
          Text(body, style: FiType.body.copyWith(color: fiInk2(context))),
          if (hint != null) ...[
            const SizedBox(height: FiSpace.s2),
            Text(hint!, style: FiType.caption.copyWith(color: fiInk3(context))),
          ],
          if (acao != null) ...[
            const SizedBox(height: FiSpace.s6),
            FiActions(primary: acao, secondary: secondary),
          ],
        ],
      ),
    );
  }
}

class FiEmptyLine extends StatelessWidget {
  const FiEmptyLine(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: FiSpace.s2),
      child: Text(text, style: FiType.body.copyWith(color: fiInk2(context))),
    );
  }
}
