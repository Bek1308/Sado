import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';

final sadoModeProvider = NotifierProvider<SadoModeSetting, SadoMode>(
  SadoModeSetting.new,
);

class SadoModeSetting extends Notifier<SadoMode> {
  @override
  SadoMode build() => SadoMode.personal;

  SadoMode get selected => state;
  set selected(SadoMode mode) => state = mode;
}
