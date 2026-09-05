import 'package:url_launcher/url_launcher.dart';

const String siteUrl = String.fromEnvironment(
  'SITE_URL',
  defaultValue: 'https://fiance.up.railway.app',
);

const String termsUrl = '$siteUrl/termos';
const String privacyUrl = '$siteUrl/privacidade';
const String cvmNoticeUrl = '$siteUrl/aviso-cvm';

Future<bool> abrirNoNavegador(String url) async {
  final destino = Uri.parse(url);
  if (!await canLaunchUrl(destino)) return false;
  return launchUrl(destino, mode: LaunchMode.externalApplication);
}
