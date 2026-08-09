import 'package:flutter/material.dart';

class AssetsScreen extends StatelessWidget {
  const AssetsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Meus Ativos')),
      body: const Center(child: Text('Carteira: posições, quantidade e preço médio')),
    );
  }
}
