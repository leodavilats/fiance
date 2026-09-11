import 'package:flutter/material.dart';

import '../../core/theme.dart';

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
    final pergunta = question;

    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (pergunta != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  FiLayout.gutter,
                  0,
                  FiLayout.gutter,
                  FiSpace.s3,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      pergunta,
                      style: fiSerif(FiType.verdictSm).copyWith(
                        color: fiInk2(context),
                      ),
                    ),
                    const SizedBox(height: FiSpace.s3),
                    Divider(
                      color: Theme.of(context).dividerColor,
                      height: 1,
                      thickness: 1,
                    ),
                  ],
                ),
              ),
            Expanded(child: child),
          ],
        ),
      ),
    );
  }
}
