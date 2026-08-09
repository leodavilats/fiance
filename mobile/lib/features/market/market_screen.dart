import 'package:flutter/material.dart';

class MarketScreen extends StatelessWidget {
  const MarketScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mercado')),
      body: const Center(child: Text('Oportunidades, Segmentos, Investir, Ferramentas')),
    );
  }
}
