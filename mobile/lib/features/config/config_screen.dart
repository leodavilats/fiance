import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';

class ConfigScreen extends ConsumerWidget {
  const ConfigScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Configurações')),
      body: Column(
        children: [
          if (user != null)
            ListTile(
              leading: CircleAvatar(
                backgroundImage: user.picture.isNotEmpty ? NetworkImage(user.picture) : null,
                child: user.picture.isEmpty ? Text(user.name.characters.first) : null,
              ),
              title: Text(user.name),
              subtitle: Text(user.email),
            ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Sair'),
            onTap: () async {
              await ref.read(authServiceProvider).signOut();
              ref.read(currentUserProvider.notifier).state = null;
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
    );
  }
}
