import 'package:flutter/material.dart';

class FiSwitch extends StatelessWidget {
  const FiSwitch({
    super.key,
    required this.label,
    required this.value,
    required this.onChanged,
  });

  final String label;
  final bool value;
  final ValueChanged<bool>? onChanged;

  @override
  Widget build(BuildContext context) {
    return MergeSemantics(
      child: Semantics(
        label: label,
        child: Switch(value: value, onChanged: onChanged),
      ),
    );
  }
}

class FiSlider extends StatelessWidget {
  const FiSlider({
    super.key,
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    required this.format,
    required this.onChanged,
    this.divisions,
  });

  final String label;
  final double value;
  final double min;
  final double max;
  final int? divisions;
  final String Function(double) format;
  final ValueChanged<double>? onChanged;

  @override
  Widget build(BuildContext context) {
    return Slider(
      value: value.clamp(min, max),
      min: min,
      max: max,
      divisions: divisions,
      label: format(value),
      semanticFormatterCallback: (v) => '$label: ${format(v)}',
      onChanged: onChanged,
    );
  }
}
