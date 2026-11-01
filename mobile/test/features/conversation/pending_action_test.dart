import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/pending_action.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

const _typeTask = PendingAction(
  id: 'a1',
  description: "Type into 'Muse Code': write the README",
);

final class _Repository implements ConversationRepository {
  final asked = <String>[];
  final confirmed = <(String, String)>[];
  final cancelled = <String>[];

  @override
  Future<Result<SadoReply>> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) async {
    asked.add(conversation.last.text);
    return const Ok(
      SadoReply(text: 'Agentga yozaymi?', pendingAction: _typeTask),
    );
  }

  @override
  Future<Result<SadoReply>> confirmAction(
    String actionId,
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) async {
    confirmed.add((actionId, conversation.last.text));
    return const Ok(SadoReply(text: "Bo'ldi, agent ishlayapti."));
  }

  @override
  Future<Result<void>> cancelAction(String actionId) async {
    cancelled.add(actionId);
    return const Ok(null);
  }
}

Future<(ConversationController, _Repository, ProviderContainer)>
_waitingForYes() async {
  final repository = _Repository();
  final container = ProviderContainer(
    overrides: [conversationRepositoryProvider.overrideWithValue(repository)],
  );
  addTearDown(container.dispose);
  final controller = container.read(conversationControllerProvider.notifier);
  await controller.ask(
    'Agentga README yozishni ayt',
    SpokenLanguage.uzbek,
    SadoMode.work,
  );
  return (controller, repository, container);
}

void main() {
  test('remembers what Sado is waiting for a yes on', () async {
    final (controller, _, _) = await _waitingForYes();

    expect(controller.pendingAction?.id, 'a1');
  });

  test('a spoken yes runs the action', () async {
    final (controller, repository, _) = await _waitingForYes();

    final reply = await controller.ask(
      'Ha, qil',
      SpokenLanguage.uzbek,
      SadoMode.work,
    );

    expect(repository.confirmed, [('a1', 'Ha, qil')]);
    expect(reply?.text, "Bo'ldi, agent ishlayapti.");
    expect(controller.pendingAction, isNull);
  });

  test('a no cancels it and Sado says so in the same language', () async {
    final (controller, repository, container) = await _waitingForYes();

    final reply = await controller.ask(
      "Yo'q",
      SpokenLanguage.uzbek,
      SadoMode.work,
    );

    expect(repository.cancelled, ['a1']);
    expect(repository.confirmed, isEmpty);
    expect(reply?.text, 'Mayli, bekor qildim.');
    expect(
      container.read(conversationControllerProvider).messages.last.text,
      'Mayli, bekor qildim.',
    );
  });

  test('anything else is a new request, not an answer', () async {
    final (controller, repository, _) = await _waitingForYes();

    await controller.ask(
      'Avval ob-havo qanday ekanini ayt',
      SpokenLanguage.uzbek,
      SadoMode.work,
    );

    expect(repository.confirmed, isEmpty);
    expect(repository.asked.last, 'Avval ob-havo qanday ekanini ayt');
  });

  test('the Yes button answers in the user language', () async {
    final (controller, repository, _) = await _waitingForYes();

    await controller.answer(
      yes: true,
      language: SpokenLanguage.tajik,
      mode: SadoMode.work,
    );

    expect(repository.confirmed, [('a1', 'Бале')]);
  });
}
