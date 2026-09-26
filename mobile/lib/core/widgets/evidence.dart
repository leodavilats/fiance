import 'package:flutter/material.dart';

import '../theme.dart';

class FiEvidence extends StatelessWidget {
  const FiEvidence({super.key, required this.reasons, this.limit = 3});

  final List<String> reasons;

  final int limit;

  static List<String> rest(List<String> reasons, {int limit = 3}) =>
      reasons.length > limit ? reasons.sublist(limit) : const [];

  @override
  Widget build(BuildContext context) {
    final mostradas = reasons.take(limit).toList();
    if (mostradas.isEmpty) return const SizedBox.shrink();

    final fio = Theme.of(context).colorScheme.outlineVariant;

    return Semantics(
      container: true,
      label: 'Por que esta leitura',
      child: Container(
        padding: const EdgeInsets.only(left: FiSpace.s3),
        decoration: BoxDecoration(
          border: Border(left: BorderSide(color: fio, width: 2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < mostradas.length; i++)
              Padding(
                padding: EdgeInsets.only(bottom: i == mostradas.length - 1 ? 0 : FiSpace.s2),
                child: Text(
                  mostradas[i],
                  style: FiType.body.copyWith(color: fiInk2(context)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
