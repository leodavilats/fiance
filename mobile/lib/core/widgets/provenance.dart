import 'package:flutter/material.dart';

import '../theme.dart';
import '../product_events.dart';

class FiProvenance extends StatelessWidget {
  const FiProvenance({
    super.key,
    this.summary = 'Como calculamos',
    this.method,
    this.source,
    this.asOf,
    this.limitation,
  });

  final String summary;
  final String? method;
  final String? source;

  final String? asOf;

  final String? limitation;

  bool get _hasContent =>
      (method ?? source ?? asOf ?? limitation) != null;

  void _open(BuildContext context) {
    trackEvent(context, 'why_this_opened');
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(summary, style: FiType.title),
              const SizedBox(height: FiSpace.s4),
              _Field(label: 'Método', value: method),
              _Field(label: 'Fonte', value: source),
              _Field(label: 'Momento', value: asOf),
              _Field(label: 'Limitação', value: limitation),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!_hasContent) return const SizedBox.shrink();

    return Semantics(
      button: true,
      label: '$summary. Abre método, fonte e limitações.',
      child: InkWell(
        onTap: () => _open(context),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
          child: Row(
            children: [
              Icon(Icons.info_outline, size: 14, color: fiInk3(context)),
              const SizedBox(width: FiSpace.s2),
              Expanded(
                child: Text(
                  summary,
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({required this.label, required this.value});

  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) {
    final texto = value;
    if (texto == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: FiType.eyebrow.copyWith(color: fiInk3(context)),
          ),
          const SizedBox(height: FiSpace.s1),
          Text(texto, style: FiType.body.copyWith(color: fiInk2(context))),
        ],
      ),
    );
  }
}
