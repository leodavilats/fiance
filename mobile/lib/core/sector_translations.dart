import 'vocabulary.dart';

String translateSector(String? sector) {
  if (sector == null || sector.isEmpty) return '—';
  return fiSetores[sector] ?? fiSetorApelidos[sector] ?? sector;
}
