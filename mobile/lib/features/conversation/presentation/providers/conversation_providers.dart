import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/conversation/data/datasources/conversation_remote_data_source.dart';
import 'package:sado/features/conversation/data/repositories/conversation_repository_impl.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/conversation/domain/usecases/ask_sado.dart';
import 'package:sado/features/lists/presentation/providers/list_providers.dart';
import 'package:sado/features/memory/presentation/providers/memory_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final conversationRepositoryProvider = Provider<ConversationRepository>(
  (ref) => ConversationRepositoryImpl(
    ConversationRemoteDataSource(ref.watch(httpClientProvider)),
  ),
);

final askSadoProvider = Provider<AskSado>(
  (ref) => AskSado(ref.watch(conversationRepositoryProvider)),
);

final conversationControllerProvider =
    NotifierProvider<ConversationController, ConversationState>(
      ConversationController.new,
    );

final class ConversationState {
  const ConversationState({
    this.messages = const [],
    this.isThinking = false,
    this.error,
    this.lastReply,
  });

  final List<ChatMessage> messages;
  final bool isThinking;
  final String? error;

  /// Sado's latest answer with what it did, so the screen can confirm it
  /// whether the user typed or talked.
  final SadoReply? lastReply;
}

class ConversationController extends Notifier<ConversationState> {
  /// Sado only needs the recent exchange to answer naturally.
  static const _contextSize = 20;

  @override
  ConversationState build() => const ConversationState();

  /// Sends [text] to Sado and returns the reply, or `null` when Sado could
  /// not answer.
  Future<SadoReply?> ask(
    String text,
    SpokenLanguage language,
    SadoMode mode,
  ) async {
    final messages = [
      ...state.messages,
      ChatMessage(speaker: ChatSpeaker.user, text: text),
    ];
    state = ConversationState(messages: messages, isThinking: true);

    final context = messages.length > _contextSize
        ? messages.sublist(messages.length - _contextSize)
        : messages;
    final result = await ref
        .read(askSadoProvider)
        .call(context, language, mode);

    switch (result) {
      case Ok(:final value):
        state = ConversationState(
          messages: [
            ...messages,
            ChatMessage(speaker: ChatSpeaker.sado, text: value.text),
          ],
          lastReply: value,
        );
        if (value.remembered.isNotEmpty) {
          ref.invalidate(memoriesControllerProvider);
        }
        if (value.listsChanged) ref.invalidate(listsControllerProvider);
        return value;
      case Err(:final failure):
        state = ConversationState(messages: messages, error: failure.message);
        return null;
    }
  }

  /// Shows a photographed paper and Sado's explanation of it, without
  /// asking the agent again.
  void showExplanation(String explanation) {
    state = ConversationState(
      messages: [
        ...state.messages,
        const ChatMessage(
          speaker: ChatSpeaker.user,
          text: '[Photo of a paper]',
        ),
        ChatMessage(speaker: ChatSpeaker.sado, text: explanation),
      ],
    );
  }

  void startOver() => state = const ConversationState();
}
