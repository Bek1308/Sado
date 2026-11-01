import 'package:sado/features/phone/domain/entities/phone_action.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

/// What Sado says when the phone could not do what it promised, or `null`
/// when it went fine.
String? phoneOutcomeMessage(
  PhoneOutcome outcome,
  PhoneAction action,
  SpokenLanguage language,
) {
  final name = action.subject;
  return switch (outcome) {
    PhoneOutcome.done => null,
    PhoneOutcome.contactNotFound => switch (language) {
      SpokenLanguage.uzbek => 'Kontaktlaringizda «$name» topilmadi.',
      SpokenLanguage.tajik => 'Дар тамосҳоятон «$name» ёфт нашуд.',
      SpokenLanguage.russian => 'Не нашёл «$name» в ваших контактах.',
      SpokenLanguage.english => 'I could not find "$name" in your contacts.',
    },
    PhoneOutcome.appNotFound => switch (language) {
      SpokenLanguage.uzbek => 'Telefoningizda «$name» topilmadi.',
      SpokenLanguage.tajik => 'Дар телефонатон «$name» ёфт нашуд.',
      SpokenLanguage.russian => 'Не нашёл «$name» на телефоне.',
      SpokenLanguage.english => 'I could not find "$name" on your phone.',
    },
    PhoneOutcome.noPermission => switch (language) {
      SpokenLanguage.uzbek => 'Buning uchun kontaktlarga ruxsat kerak.',
      SpokenLanguage.tajik => 'Барои ин иҷозат ба тамосҳо лозим аст.',
      SpokenLanguage.russian => 'Для этого нужен доступ к контактам.',
      SpokenLanguage.english => 'I need access to your contacts for that.',
    },
    PhoneOutcome.failed => switch (language) {
      SpokenLanguage.uzbek => 'Telefonda buni bajara olmadim.',
      SpokenLanguage.tajik => 'Дар телефон инро иҷро карда натавонистам.',
      SpokenLanguage.russian => 'Не получилось сделать это на телефоне.',
      SpokenLanguage.english => 'I could not do that on the phone.',
    },
  };
}
