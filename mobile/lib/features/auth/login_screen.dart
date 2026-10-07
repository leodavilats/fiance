import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/app_logo.dart';
import '../../core/app_wordmark.dart';
import '../../core/legal_links.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/brand_background.dart';
import '../../core/auth_service.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  bool _loading = false;
  String? _error;

  static const _whatItDoes = [
    ('Mês', 'o que entrou, o que saiu e o que ainda vence'),
    ('Sobra', 'a ordem em que o que ficou deve ser usado'),
    ('Patrimônio', 'preço justo, margem de segurança e IR apurado'),
  ];

  Future<void> _handleSignIn() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final user = await ref.read(authServiceProvider).signInWithGoogle();
      if (!mounted) return;
      ref.read(currentUserProvider.notifier).state = user;
      context.go('/dashboard');
    } on SignInCancelled {
      return;
    } catch (e) {
      if (mounted) setState(() => _error = fiErrorMessage(e, action: 'entrar'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final hairline = Theme.of(context).dividerColor;

    return Scaffold(
      body: BrandBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(FiSpace.s6),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const AppLogo(size: 72),
                    const SizedBox(height: FiSpace.s5),
                    AppWordmark(height: 30, color: fiInk1(context)),
                    const SizedBox(height: FiSpace.s3),
                    Text(
                      'Da sobra do mês ao próximo aporte, com a conta à vista.',
                      style: FiType.bodyLg.copyWith(color: fiInk2(context)),
                    ),

                    const SizedBox(height: FiSpace.s8),
                    for (final (titulo, responde) in _whatItDoes) ...[
                      Divider(color: hairline, height: 1, thickness: 1),
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: FiSpace.s3),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              titulo,
                              style: FiType.title.copyWith(color: fiInk1(context)),
                            ),
                            const SizedBox(height: FiSpace.s1),
                            Text(
                              responde,
                              style: FiType.caption.copyWith(color: fiInk2(context)),
                            ),
                          ],
                        ),
                      ),
                    ],
                    Divider(color: hairline, height: 1, thickness: 1),

                    const SizedBox(height: FiSpace.s8),
                    if (_error != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: FiSpace.s4),
                        child: Text(
                          _error!,
                          style: FiType.body.copyWith(
                            color: fiStateColor(
                              FiState.attention,
                              Theme.of(context).brightness,
                            ),
                          ),
                        ),
                      ),
                    FiButton.primary(
                      label: 'Continuar com Google',
                      expand: true,
                      busy: _loading,
                      onPressed: _handleSignIn,
                    ),

                    const SizedBox(height: FiSpace.s5),
                    Text(
                      'Ferramenta de análise, não consultoria. Não há garantia de retorno.',
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                    const SizedBox(height: FiSpace.s1),
                    const _LegalConsent(),
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

class _LegalConsent extends StatelessWidget {
  const _LegalConsent();

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      explicitChildNodes: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Ao entrar você aceita os documentos:',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
          const Wrap(
            spacing: FiSpace.s5,
            children: [
              _LegalLink(label: 'Termos', url: termsUrl),
              _LegalLink(label: 'Política de Privacidade', url: privacyUrl),
            ],
          ),
        ],
      ),
    );
  }
}

class _LegalLink extends StatelessWidget {
  const _LegalLink({required this.label, required this.url});

  final String label;
  final String url;

  @override
  Widget build(BuildContext context) {
    return TextButton(
      style: TextButton.styleFrom(
        padding: EdgeInsets.zero,
        minimumSize: const Size(FiLayout.minTouchTarget, FiLayout.minTouchTarget),
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        foregroundColor: fiInk2(context),
        textStyle: fiSans(FiType.caption).copyWith(
          decoration: TextDecoration.underline,
        ),
      ),
      onPressed: () async {
        final abriu = await openInBrowser(url);
        if (!abriu && context.mounted) {
          fiNotify(context, 'Não foi possível abrir $url');
        }
      },
      child: Text(label),
    );
  }
}
