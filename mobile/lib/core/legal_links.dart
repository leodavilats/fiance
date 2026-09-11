import 'package:url_launcher/url_launcher.dart';

const String siteUrl = String.fromEnvironment(
  'SITE_URL',
  defaultValue: 'https://fiance.up.railway.app',
);

const String termsUrl = '$siteUrl/termos';
const String privacyUrl = '$siteUrl/privacidade';
const String cvmNoticeUrl = '$siteUrl/aviso-cvm';

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
