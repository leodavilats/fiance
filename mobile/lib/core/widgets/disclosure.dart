import 'package:flutter/material.dart';

import '../theme.dart';

class FiDisclosure extends StatefulWidget {
  const FiDisclosure({
    super.key,
    required this.title,
    required this.child,
    this.value,
    this.valueColor,
    this.detail,
    this.initiallyOpen = false,
    this.leading,
    this.rule = true,
  });

  final String title;

  final Widget child;

  final String? value;

  final Color? valueColor;

  final String? detail;

  final bool initiallyOpen;

  final Widget? leading;

  final bool rule;

  @override
  State<FiDisclosure> createState() => _FiDisclosureState();
}

class _FiDisclosureState extends State<FiDisclosure> {
  late bool _isOpen = widget.initiallyOpen;

  @override
  Widget build(BuildContext context) {
    final cabecalho = Padding(
      padding: const EdgeInsets.symmetric(vertical: FiSpace.s3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (widget.leading != null) ...[
            widget.leading!,
            const SizedBox(width: FiSpace.s3),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.title,
                  style: FiType.body.copyWith(color: fiInk1(context)),
                ),
                if (widget.detail != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      widget.detail!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                  ),
              ],
            ),
          ),
          if (widget.value != null) ...[
            const SizedBox(width: FiSpace.s3),
            Text(
              widget.value!,
              style: FiType.figure.copyWith(
                color: widget.valueColor ?? fiInk1(context),
              ),
            ),
          ],
          const SizedBox(width: FiSpace.s2),
          AnimatedRotation(
            turns: _isOpen ? 0.5 : 0,
            duration: FiMotion.fast,
            curve: FiMotion.easeEnter,
            child: Icon(
              Icons.expand_more,
              size: 20,
              color: fiInk3(context),
            ),
          ),
        ],
      ),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.rule)
          Divider(
            color: Theme.of(context).dividerColor,
            height: 1,
            thickness: 1,
          ),
        Semantics(
          button: true,
          expanded: _isOpen,
          label: widget.title,
          child: ExcludeSemantics(
            child: InkWell(
              onTap: () => setState(() => _isOpen = !_isOpen),
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  minHeight: FiLayout.minTouchTarget,
                ),
                child: cabecalho,
              ),
            ),
          ),
        ),
        AnimatedSize(
          duration: FiMotion.base,
          curve: FiMotion.easeEnter,
          alignment: Alignment.topCenter,
          child: _isOpen
              ? Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s4),
                  child: widget.child,
                )
              : const SizedBox(width: double.infinity),
        ),
      ],
    );
  }
}

class FiGroupDisclosure extends StatefulWidget {
  const FiGroupDisclosure({
    super.key,
    required this.label,
    required this.child,
    this.trailing,
    this.count,
    this.initiallyOpen = true,
  });

  final String label;

  final Widget child;

  final String? trailing;

  final int? count;

  final bool initiallyOpen;

  @override
  State<FiGroupDisclosure> createState() => _FiGroupDisclosureState();
}

class _FiGroupDisclosureState extends State<FiGroupDisclosure> {
  late bool _isOpen = widget.initiallyOpen;

  @override
  Widget build(BuildContext context) {
    final titulo = widget.count == null
        ? widget.label.toUpperCase()
        : '${widget.label.toUpperCase()} · ${widget.count}';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
        Semantics(
          button: true,
          expanded: _isOpen,
          header: true,
          label: titulo,
          child: ExcludeSemantics(
            child: InkWell(
              onTap: () => setState(() => _isOpen = !_isOpen),
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  minHeight: FiLayout.minTouchTarget,
                ),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: FiSpace.s3),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      AnimatedRotation(
                        turns: _isOpen ? 0 : -0.25,
                        duration: FiMotion.fast,
                        curve: FiMotion.easeEnter,
                        child: Icon(
                          Icons.expand_more,
                          size: 18,
                          color: fiInk3(context),
                        ),
                      ),
                      const SizedBox(width: FiSpace.s2),
                      Expanded(
                        child: Text(
                          titulo,
                          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                        ),
                      ),
                      if (widget.trailing != null)
                        Text(
                          widget.trailing!,
                          style: FiType.caption.copyWith(color: fiInk2(context)),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
        AnimatedSize(
          duration: FiMotion.base,
          curve: FiMotion.easeEnter,
          alignment: Alignment.topCenter,
          child: _isOpen
              ? Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s5),
                  child: widget.child,
                )
              : const SizedBox(width: double.infinity),
        ),
      ],
    );
  }
}
