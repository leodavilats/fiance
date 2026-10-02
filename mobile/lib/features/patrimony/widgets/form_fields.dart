import 'package:flutter/material.dart';

import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/ticker_autocomplete_field.dart';

class FiTickerFormField extends StatelessWidget {
  const FiTickerFormField({
    super.key,
    required this.controller,
    this.labelText = 'Ticker',
    this.onSelected,
  });

  final TextEditingController controller;
  final String labelText;
  final ValueChanged<TickerSuggestion>? onSelected;

  @override
  Widget build(BuildContext context) {
    return FormField<String>(
      validator: (_) => controller.text.trim().isEmpty ? 'Informe o ticker do ativo' : null,
      builder: (state) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          TickerAutocompleteField(
            controller: controller,
            labelText: labelText,
            onSelected: onSelected,
          ),
          if (state.hasError)
            Padding(
              padding: const EdgeInsets.only(top: FiSpace.s1),
              child: Text(
                state.errorText!,
                style: FiType.caption.copyWith(color: Theme.of(context).colorScheme.error),
              ),
            ),
        ],
      ),
    );
  }
}

class FiInlineError extends StatelessWidget {
  const FiInlineError(this.message, {super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Padding(
        padding: const EdgeInsets.only(bottom: FiSpace.s3),
        child: Text(
          message,
          style: FiType.body.copyWith(
            color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
          ),
        ),
      ),
    );
  }
}
