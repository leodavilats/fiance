import 'package:flutter/material.dart';

import '../../core/design_tokens.dart';

class ToolScreen extends StatelessWidget {
  const ToolScreen({
    super.key,
    required this.title,
    required this.child,
    this.question,
  });

  final String title;

  final String? question;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final ink3 = isDark ? FiColors.darkInk3 : FiColors.lightInk3;

    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (question != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  FiSpace.s4,
                  0,
                  FiSpace.s4,
                  FiSpace.s2,
                ),
                child: Text(question!, style: FiType.body.copyWith(color: ink3)),
              ),
            Expanded(child: child),
          ],
        ),
      ),
    );
  }
}
