import 'package:url_launcher/url_launcher.dart';

const String siteUrl = String.fromEnvironment(
  'SITE_URL',
  defaultValue: 'https://fiance.up.railway.app',
);

const String termsUrl = '$siteUrl/termos';
const String privacyUrl = '$siteUrl/privacidade';
const String cvmNoticeUrl = '$siteUrl/aviso-cvm';

/// Abre a pagina no navegador do aparelho.
///
/// Nao passa por `canLaunchUrl`: desde o Android 11 ele responde `false` para `https` a menos
/// que o manifesto declare a visibilidade do pacote, e a tela ficava sem reacao nenhuma. A
/// declaracao esta no `AndroidManifest.xml`, e aqui a tentativa e direta -- quem falha e o
/// `launchUrl`, que diz por que.
Future<bool> abrirNoNavegador(String url) async {
  try {
    return await launchUrl(
      Uri.parse(url),
      mode: LaunchMode.externalApplication,
    );
  } catch (_) {
    return false;
  }
}
