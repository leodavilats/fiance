import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Casca de navegação com as 4 abas espelhando o app web
/// (Dashboard, Meus Ativos, Mercado, Configurações).
class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) => navigationShell.goBranch(
          index,
          initialLocation: index == navigationShell.currentIndex,
        ),
        // Ícones alinhados conceitualmente aos do web (Lucide):
        // layout-dashboard, briefcase, target, settings.
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.work_outline),
            label: 'Meus Ativos',
          ),
          NavigationDestination(
            icon: Icon(Icons.track_changes_outlined),
            label: 'Mercado',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            label: 'Config',
          ),
        ],
      ),
    );
  }
}
