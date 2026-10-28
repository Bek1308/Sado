import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final class _FakeRepository implements ConversationRepository {
  _FakeRepository(this.result);

  final Result<String> result;
  final sent = <List<ChatMessage>>[];

  @override
  Future<Result<String>> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
  ) async {
    sent.add(conversation);
    return result;
  }
}

ProviderContainer _container(_FakeRepository repository) {
  final container = ProviderContainer(
    overrides: [conversationRepositoryProvider.overrideWithValue(repository)],
  );
  addTearDown(container.dispose);
  return container;
}

void main() {
  test('keeps the exchange and returns the reply', () async {
    final repository = _FakeRepository(const Ok('Salom!'));
    final container = _container(repository);

    final reply = await container
        .read(conversationControllerProvider.notifier)
        .ask('salom', SpokenLanguage.uzbek);

    expect(reply, 'Salom!');
    final messages = container.read(conversationControllerProvider).messages;
    expect(
      [for (final m in messages) (m.speaker, m.text)],
      [
        (ChatSpeaker.user, 'salom'),
        (ChatSpeaker.sado, 'Salom!'),
      ],
    );
  });

  test('sends earlier messages as context', () async {
    final repository = _FakeRepository(const Ok('ok'));
    final controller = _container(
      repository,
    ).read(conversationControllerProvider.notifier);

    await controller.ask('birinchi', SpokenLanguage.uzbek);
    await controller.ask('ikkinchi', SpokenLanguage.uzbek);

    expect(repository.sent.last.map((m) => m.text), [
      'birinchi',
      'ok',
      'ikkinchi',
    ]);
  });

  test('shows why Sado could not answer', () async {
    final container = _container(
      _FakeRepository(const Err(ServerFailure('Sado cannot think right now'))),
    );

    final reply = await container
        .read(conversationControllerProvider.notifier)
        .ask('salom', SpokenLanguage.uzbek);

    expect(reply, isNull);
    expect(
      container.read(conversationControllerProvider).error,
      'Sado cannot think right now',
    );
  });
}
