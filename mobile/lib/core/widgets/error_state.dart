import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../design_tokens.dart';
import '../theme.dart';

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
    if (status == 401 || status == 403) {
      return 'Sua sessão expirou. Entre novamente para continuar.';
    }
    if (status == 404) {
      return 'Não encontramos o que você pediu.';
    }
    if (status != null && status >= 500) {
      return 'O serviço está instável no momento. Tente de novo em instantes.';
    }

    final detail = error.response?.data;
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(FiSpace.s6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title ?? 'Algo não carregou',
              style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              fiErrorMessage(error, action: action),
              style: FiType.body.copyWith(color: ink2),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: FiSpace.s4),
              FilledButton(onPressed: onRetry, child: const Text('Tentar de novo')),
            ],
          ],
        ),
      ),
    );
  }
}
