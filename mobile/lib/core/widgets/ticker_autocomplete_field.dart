import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models.dart';
import '../providers.dart';
import '../theme.dart';

class TickerAutocompleteField extends ConsumerStatefulWidget {
  const TickerAutocompleteField({
    super.key,
    required this.controller,
    this.labelText = 'Ticker',
    this.onSelected,
  });

  final TextEditingController controller;
  final String labelText;
  final ValueChanged<TickerSuggestion>? onSelected;

  @override
  ConsumerState<TickerAutocompleteField> createState() =>
      _TickerAutocompleteFieldState();
}

class _TickerAutocompleteFieldState
    extends ConsumerState<TickerAutocompleteField> {
  List<TickerSuggestion> _suggestions = [];
  Timer? _debounce;
  bool _disposed = false;

  @override
  void dispose() {
    _disposed = true;
    _debounce?.cancel();
    super.dispose();
  }

  void _onChanged(String value) {
    _debounce?.cancel();
    if (value.trim().isEmpty) {
      setState(() => _suggestions = []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () async {
      final results = await ref
          .read(apiRepositoryProvider)
          .searchTickers(value);
      if (_disposed) return;
      setState(() => _suggestions = results);
    });
  }

  void _select(TickerSuggestion s) {
    widget.controller.text = s.ticker;
    setState(() => _suggestions = []);
    widget.onSelected?.call(s);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        TextField(
          controller: widget.controller,
          textCapitalization: TextCapitalization.characters,
          decoration: InputDecoration(labelText: widget.labelText),
          onChanged: _onChanged,
        ),
        if (_suggestions.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: FiSpace.s1),
            constraints: const BoxConstraints(maxHeight: 200),
            decoration: BoxDecoration(
              color: fiGround1(Theme.of(context).brightness),
              border: Border.all(color: Theme.of(context).colorScheme.outline),
              borderRadius: BorderRadius.circular(FiRadius.md),
            ),
            child: ListView.builder(
              shrinkWrap: true,
              padding: EdgeInsets.zero,
              itemCount: _suggestions.length,
              itemBuilder: (context, index) {
                final s = _suggestions[index];
                return Semantics(
                  button: true,
                  label: '${s.ticker}${s.name.isEmpty ? '' : ', ${s.name}'}',
                  child: InkWell(
                    onTap: () => _select(s),
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(
                        minHeight: FiLayout.minTouchTarget,
                      ),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: FiSpace.s3,
                          vertical: FiSpace.s2,
                        ),
                        child: Row(
                          children: [
                            Text(
                              s.ticker,
                              style: FiType.ticker.copyWith(
                                color: fiInk1(context),
                              ),
                            ),
                            if (s.name.isNotEmpty) ...[
                              const SizedBox(width: FiSpace.s2),
                              Expanded(
                                child: Text(
                                  s.name,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: FiType.caption.copyWith(
                                    color: fiInk2(context),
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }
}
