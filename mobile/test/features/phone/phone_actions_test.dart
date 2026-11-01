import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/phone/domain/entities/phone_action.dart';
import 'package:sado/features/phone/domain/repositories/phone_control.dart';
import 'package:sado/features/phone/presentation/providers/phone_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

const _callMother = PhoneAction(kind: 'call', details: {'contact': 'Onam'});

final class _Repository implements ConversationRepository {
  @override
  Future<Result<SadoReply>> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) async => const Ok(
    SadoReply(
      text: "Onangizga qo'ng'iroq qilyapman.",
      phoneActions: [_callMother],
    ),
  );

  @override
  Future<Result<SadoReply>> confirmAction(
    String actionId,
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) => throw UnimplementedError();

  @override
  Future<Result<void>> cancelAction(String actionId) =>
      throw UnimplementedError();
}

final class _Phone implements PhoneControl {
  _Phone(this.outcome);

  final PhoneOutcome outcome;
  final performed = <PhoneAction>[];

  @override
  bool get supported => true;

  @override
  Future<PhoneOutcome> perform(PhoneAction action) async {
    performed.add(action);
    return outcome;
  }
}

Future<(SadoReply?, _Phone, ProviderContainer)> _askToCall(
  PhoneOutcome outcome,
) async {
  final phone = _Phone(outcome);
  final container = ProviderContainer(
    overrides: [
      conversationRepositoryProvider.overrideWithValue(_Repository()),
      phoneControlProvider.overrideWithValue(phone),
    ],
  );
  addTearDown(container.dispose);
  final reply = await container
      .read(conversationControllerProvider.notifier)
      .ask("Onamga qo'ng'iroq qil", SpokenLanguage.uzbek, SadoMode.personal);
  return (reply, phone, container);
}

void main() {
  test('the phone does what Sado said', () async {
    final (reply, phone, _) = await _askToCall(PhoneOutcome.done);

    expect(phone.performed.single.details['contact'], 'Onam');
    expect(reply?.text, "Onangizga qo'ng'iroq qilyapman.");
  });

  test('Sado admits it when the phone could not do it', () async {
    final (reply, _, container) = await _askToCall(
      PhoneOutcome.contactNotFound,
    );

    expect(reply?.text, 'Kontaktlaringizda «Onam» topilmadi.');
    expect(
      container.read(conversationControllerProvider).messages.last.text,
      'Kontaktlaringizda «Onam» topilmadi.',
    );
  });
}
