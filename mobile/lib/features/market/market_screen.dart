import 'package:flutter/material.dart';

import 'ferramentas_tab.dart';
import 'investir_tab.dart';
import 'opportunities_tab.dart';
import 'sectors_tab.dart';

class MarketScreen extends StatelessWidget {
  const MarketScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Mercado'),
          bottom: const TabBar(
            isScrollable: true,
            tabs: [
              Tab(text: 'Oportunidades'),
              Tab(text: 'Segmentos'),
              Tab(text: 'Investir'),
              Tab(text: 'Ferramentas'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            OpportunitiesTab(),
            SectorsTab(),
            InvestirTab(),
            FerramentasTab(),
          ],
        ),
      ),
    );
  }
}
