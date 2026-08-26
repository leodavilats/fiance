import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/brand_background.dart';
import '../../core/widgets/brand_loading_indicator.dart';

class SplashScreen extends ConsumerWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(authStatusProvider, (previous, next) {
      next.when(
        data: (user) {
          if (!context.mounted) return;
          context.go(user != null ? '/dashboard' : '/login');
        },
        loading: () {},
        error: (_, _) {
          if (context.mounted) context.go('/login');
        },
      );
    });

    return Scaffold(
      body: BrandBackground(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 320),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const BrandLoadingIndicator(size: 72),
                  const SizedBox(height: 20),
                  const Text(
                    'fiance',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Ações, FIIs, BDRs, ETFs e renda fixa — tudo em um só assistente',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: fiInk2(context),
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
