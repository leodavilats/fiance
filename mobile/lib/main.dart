import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/providers.dart';
import 'core/router.dart';
import 'core/telemetry.dart';
import 'core/theme.dart';
import 'core/theme_provider.dart';
import 'firebase_options.dart';

void main() async {
  await runWithTelemetry(() async {
    WidgetsFlutterBinding.ensureInitialized();
    try {
      await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      );
    } catch (e) {
      debugPrint('Firebase não inicializado: $e');
    }
    runApp(const ProviderScope(child: FianceApp()));
  });
}

class FianceApp extends ConsumerStatefulWidget {
  const FianceApp({super.key});

  @override
  ConsumerState<FianceApp> createState() => _FianceAppState();
}

class _FianceAppState extends ConsumerState<FianceApp> {
  final _mensageiro = GlobalKey<ScaffoldMessengerState>();
  StreamSubscription<void>? _fimDaSessao;

  @override
  void initState() {
    super.initState();
    _fimDaSessao = ref.read(authServiceProvider).sessionEnded.listen((_) {
      ref.read(currentUserProvider.notifier).state = null;
      if (appRouter.routerDelegate.currentConfiguration.uri.path == '/login') return;
      appRouter.go('/login');
      _mensageiro.currentState
        ?..hideCurrentSnackBar()
        ..showSnackBar(
          const SnackBar(content: Text('Sua sessão terminou. Entre de novo para continuar.')),
        );
    });
  }

  @override
  void dispose() {
    _fimDaSessao?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final themeMode = ref.watch(themeModeProvider);
    return MaterialApp.router(
      title: 'fiance',
      scaffoldMessengerKey: _mensageiro,
      themeMode: themeMode,
      theme: buildAppTheme(Brightness.light),
      darkTheme: buildAppTheme(Brightness.dark),
      routerConfig: appRouter,
    );
  }
}
