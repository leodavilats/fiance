import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers.dart';
import '../theme.dart';
import 'button.dart';

bool fiSessionExpired(Object error) =>
    error is DioException && error.response?.statusCode == 401;

String fiErrorMessage(Object error, {String? action}) {
  final what = action ?? 'carregar estes dados';

  if (error is DioException) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'A resposta demorou demais. Sua conexão pode estar instável.';
      case DioExceptionType.connectionError:
        return 'Sem conexão com a internet. Seus dados salvos continuam intactos.';
      default:
        break;
    }

    final status = error.response?.statusCode;
    final detail = error.response?.data;
    if (status == 401) {
      return 'Sua sessão expirou. Entre novamente para continuar.';
    }
    if (status == 402) {
      final decisao = detail is Map ? detail['detail'] : null;
      final motivo = decisao is Map ? decisao['reason'] : null;
      return motivo is String && motivo.trim().isNotEmpty
          ? 'Isso passa do limite do seu plano. ${motivo.trim()}'
          : 'Isso passa do limite do seu plano.';
    }
    if (status == 403) {
      return 'Esta conta não tem permissão para $what.';
    }
    if (status == 404) {
      return 'Não encontramos o que você pediu.';
    }
    if (status != null && status >= 500) {
      return 'O serviço está instável no momento. Tente de novo em instantes.';
    }

    if (detail is Map && detail['detail'] is String) {
      return detail['detail'] as String;
    }
  }

  return 'Não conseguimos $what agora. Pode ser a conexão ou uma instabilidade na '
      'fonte de cotações.';
}

class FiErrorState extends StatelessWidget {
  const FiErrorState({
    super.key,
    required this.error,
    this.onRetry,
    this.title,
    this.action,
  });

  final Object error;
  final VoidCallback? onRetry;
  final String? title;

  final String? action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s8,
        FiLayout.gutter,
        FiSpace.s6,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title ?? 'Algo não carregou',
            style: fiSerif(FiType.verdict).copyWith(
              color: fiStateColor(FiState.attention, Theme.of(context).brightness),
            ),
          ),
          const SizedBox(height: FiSpace.s3),
          Text(
            fiErrorMessage(error, action: action),
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          if (fiSessionExpired(error)) ...[
            const SizedBox(height: FiSpace.s6),
            FiButton.primary(label: 'Entrar de novo', onPressed: () => _signInAgain(context)),
          ] else if (onRetry != null) ...[
            const SizedBox(height: FiSpace.s6),
            FiButton.secondary(label: 'Tentar de novo', onPressed: onRetry),
          ],
        ],
      ),
    );
  }

  Future<void> _signInAgain(BuildContext context) async {
    final roteador = GoRouter.maybeOf(context);
    await ProviderScope.containerOf(context, listen: false).read(signOutProvider)();
    roteador?.go('/login');
  }
}
