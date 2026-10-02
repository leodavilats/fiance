import 'package:flutter/material.dart';

import 'button.dart';
import 'error_state.dart';

void fiNotify(
  BuildContext context,
  String message, {
  String? actionLabel,
  VoidCallback? onAction,
}) {
  final mensageiro = ScaffoldMessenger.maybeOf(context);
  if (mensageiro == null) return;
  mensageiro
    ..hideCurrentSnackBar()
    ..showSnackBar(
      SnackBar(
        content: Text(message),
        action: actionLabel == null || onAction == null
            ? null
            : SnackBarAction(label: actionLabel, onPressed: onAction),
      ),
    );
}

Future<bool> fiAttempt(
  BuildContext context,
  Future<void> Function() write, {
  required String action,
  String? success,
  Future<void> Function()? undo,
}) async {
  final mensageiro = ScaffoldMessenger.maybeOf(context);

  void avisar(String texto, {String? rotulo, VoidCallback? acao}) {
    mensageiro
      ?..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(texto),
          action: rotulo == null || acao == null
              ? null
              : SnackBarAction(label: rotulo, onPressed: acao),
        ),
      );
  }

  try {
    await write();
  } catch (e) {
    avisar(fiErrorMessage(e, action: action));
    return false;
  }

  if (success != null) {
    final desfazer = undo;
    avisar(
      success,
      rotulo: desfazer == null ? null : 'Desfazer',
      acao: desfazer == null
          ? null
          : () async {
              try {
                await desfazer();
              } catch (e) {
                avisar(fiErrorMessage(e, action: 'desfazer'));
              }
            },
    );
  }
  return true;
}

Future<bool> fiConfirm(
  BuildContext context, {
  required String title,
  required String body,
  required String confirmLabel,
  bool destructive = true,
  String cancelLabel = 'Cancelar',
}) async {
  final confirmado = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: Text(body),
      actions: [
        FiButton.quiet(
          label: cancelLabel,
          onPressed: () => Navigator.pop(context, false),
        ),
        destructive
            ? FiButton.danger(
                label: confirmLabel,
                onPressed: () => Navigator.pop(context, true),
              )
            : FiButton.primary(
                label: confirmLabel,
                onPressed: () => Navigator.pop(context, true),
              ),
      ],
    ),
  );
  return confirmado == true;
}
