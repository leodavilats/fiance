import 'vocabulary.dart';

String translateSector(String? sector) {
  if (sector == null || sector.isEmpty) return '—';
  return fiSectors[sector] ?? fiSectorAliases[sector] ?? sector;
}
