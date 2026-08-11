import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models.dart';
import '../providers.dart';

/// Campo de ticker com sugestões (ticker + nome da empresa) enquanto o
/// usuário digita, buscando em `GET /universe/search`. Pensado para uso
/// dentro de diálogos — mostra a lista inline (não em overlay), evitando
/// problemas de posicionamento dentro de um `AlertDialog`.
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
            margin: const EdgeInsets.only(top: 4),
            constraints: const BoxConstraints(maxHeight: 180),
            decoration: BoxDecoration(
              border: Border.all(color: Theme.of(context).colorScheme.outline),
              borderRadius: BorderRadius.circular(8),
            ),
            child: ListView.builder(
              shrinkWrap: true,
              padding: EdgeInsets.zero,
              itemCount: _suggestions.length,
              itemBuilder: (context, index) {
                final s = _suggestions[index];
                return ListTile(
                  dense: true,
                  title: Text(
                    s.ticker,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: s.name.isNotEmpty ? Text(s.name) : null,
                  onTap: () => _select(s),
                );
              },
            ),
          ),
      ],
    );
  }
}
