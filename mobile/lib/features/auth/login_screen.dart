import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/app_logo.dart';
import '../../core/app_wordmark.dart';
import '../../core/legal_links.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/brand_background.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  bool _loading = false;
  String? _error;

  Future<void> _handleSignIn() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final user = await ref.read(authServiceProvider).signInWithGoogle();
      ref.read(currentUserProvider.notifier).state = user;
      if (mounted) context.go('/dashboard');
    } catch (e) {
      setState(() => _error = 'Falha no login: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final panelColor = scheme.surface;
    final borderColor = scheme.outline;
    final mutedColor = fiInk2(context);
    final accent = scheme.primary;

    return Scaffold(
      body: BrandBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: const AppLogo(size: 88),
                    ),
                    const SizedBox(height: 24),
                    AppWordmark(height: 32, color: Theme.of(context).colorScheme.onSurface),
                    const SizedBox(height: 10),
                    Text(
                      'Da sobra do mês ao próximo aporte, com a conta à vista',
                      textAlign: TextAlign.center,
                      style: FiType.body.copyWith(color: mutedColor),
                    ),
                    const SizedBox(height: 32),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        vertical: 18,
                        horizontal: 8,
                      ),
                      decoration: BoxDecoration(
                        color: panelColor,
                        borderRadius: BorderRadius.circular(appRadius),
                        border: Border.all(color: borderColor),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _Feature(
                            icon: Icons.insights_outlined,
                            label: 'Preço justo',
                            color: accent,
                          ),
                          _Feature(
                            icon: Icons.notifications_active_outlined,
                            label: 'Alertas',
                            color: accent,
                          ),
                          _Feature(
                            icon: Icons.school_outlined,
                            label: 'Educativo',
                            color: accent,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 28),
                    if (_error != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: Text(
                          _error!,
                          textAlign: TextAlign.center,
                          style: TextStyle(color: fiStateColor(FiState.adverse, Theme.of(context).brightness)),
                        ),
                      ),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _loading ? null : _handleSignIn,
                        icon: _loading
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.g_mobiledata, size: 26),
                        label: const Text(
                          'Continuar com Google',
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Theme.of(context).colorScheme.primary,
                          foregroundColor: Theme.of(context).colorScheme.onPrimary,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(appRadius),
                          ),
                          elevation: 0,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'Ferramenta de análise, não consultoria. Não há garantia '
                      'de retorno.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: mutedColor, fontSize: 11),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      alignment: WrapAlignment.center,
                      spacing: 4,
                      children: [
                        Text(
                          'Ao entrar você aceita os',
                          style: TextStyle(color: mutedColor, fontSize: 11),
                        ),
                        _LinkLegal(label: 'Termos', url: termsUrl),
                        Text(
                          'e a',
                          style: TextStyle(color: mutedColor, fontSize: 11),
                        ),
                        _LinkLegal(
                          label: 'Política de Privacidade',
                          url: privacyUrl,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Feature extends StatelessWidget {
  const _Feature({required this.icon, required this.label, required this.color});

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 22),
        const SizedBox(height: 6),
        Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
      ],
    );
  }
}


class _LinkLegal extends StatelessWidget {
  const _LinkLegal({required this.label, required this.url});

  final String label;
  final String url;

  @override
  Widget build(BuildContext context) {
    return TextButton(
      style: TextButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 2),
        minimumSize: const Size(0, 32),
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        textStyle: const TextStyle(fontSize: 11),
      ),
      onPressed: () async {
        final abriu = await abrirNoNavegador(url);
        if (!abriu && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Não foi possível abrir $url')),
          );
        }
      },
      child: Text(label),
    );
  }
}
