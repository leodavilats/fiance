import 'package:flutter/material.dart';

import 'ferramentas_tab.dart';
import 'opportunities_tab.dart';
import 'rebalance_tab.dart';

class MarketScreen extends StatelessWidget {
  const MarketScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Mercado'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Oportunidades'),
              Tab(text: 'Rebalanceamento'),
              Tab(text: 'Ferramentas'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            OpportunitiesTab(),
            RebalanceTab(),
            FerramentasTab(),
          ],
        ),
      ),
    );
  }
}
