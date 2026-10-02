import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models.dart';
import '../providers.dart';
import '../theme.dart';
import 'error_state.dart';

class TickerAutocompleteField extends ConsumerStatefulWidget {
  const TickerAutocompleteField({
    super.key,
    required this.controller,
    this.labelText = 'Ticker',
    this.onSelected,
    this.onChanged,
    this.onSubmitted,
    this.fieldHeight,
  });

  final TextEditingController controller;
  final String labelText;
  final ValueChanged<TickerSuggestion>? onSelected;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final double? fieldHeight;

  @override
  ConsumerState<TickerAutocompleteField> createState() =>
      _TickerAutocompleteFieldState();
}

class _TickerAutocompleteFieldState
    extends ConsumerState<TickerAutocompleteField> {
  List<TickerSuggestion> _suggestions = [];
  Object? _error;
  Timer? _debounce;
  bool _disposed = false;

  @override
  void dispose() {
    _disposed = true;
    _debounce?.cancel();
    super.dispose();
  }

  void _onChanged(String value) {
    widget.onChanged?.call(value);
    _debounce?.cancel();
    if (value.trim().isEmpty) {
      setState(() {
        _suggestions = [];
        _error = null;
      });
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () => _search(value));
  }

  Future<void> _search(String value) async {
    try {
      final results = await ref.read(apiRepositoryProvider).searchTickers(value);
      if (_disposed || widget.controller.text != value) return;
      setState(() {
        _suggestions = results;
        _error = null;
      });
    } catch (e) {
      if (_disposed || widget.controller.text != value) return;
      setState(() {
        _suggestions = [];
        _error = e;
      });
    }
  }

  void _select(TickerSuggestion s) {
    _debounce?.cancel();
    widget.controller.text = s.ticker;
    setState(() {
      _suggestions = [];
      _error = null;
    });
    widget.onSelected?.call(s);
  }

  void _submit(String value) {
    _debounce?.cancel();
    setState(() {
      _suggestions = [];
      _error = null;
    });
    widget.onSubmitted?.call(value);
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
          textInputAction: widget.onSubmitted == null ? null : TextInputAction.search,
          decoration: InputDecoration(
            labelText: widget.labelText,
            constraints: widget.fieldHeight == null
                ? null
                : BoxConstraints.tightFor(height: widget.fieldHeight),
          ),
          onChanged: _onChanged,
          onSubmitted: widget.onSubmitted == null ? null : _submit,
        ),
        if (_error case final erro?)
          Padding(
            padding: const EdgeInsets.only(top: FiSpace.s1),
            child: Text(
              fiErrorMessage(erro, action: 'buscar o ticker'),
              style: FiType.caption.copyWith(
                color: fiStateColor(FiState.attention, Theme.of(context).brightness),
              ),
            ),
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
