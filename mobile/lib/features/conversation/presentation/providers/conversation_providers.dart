import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/conversation/data/datasources/conversation_remote_data_source.dart';
import 'package:sado/features/conversation/data/repositories/conversation_repository_impl.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/consent.dart';
import 'package:sado/features/conversation/domain/entities/pending_action.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/conversation/domain/usecases/ask_sado.dart';
import 'package:sado/features/lists/presentation/providers/list_providers.dart';
import 'package:sado/features/memory/presentation/providers/memory_providers.dart';
import 'package:sado/features/phone/domain/entities/phone_action.dart';
import 'package:sado/features/phone/domain/entities/phone_outcome_message.dart';
import 'package:sado/features/phone/presentation/providers/phone_providers.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final conversationRepositoryProvider = Provider<ConversationRepository>(
  (ref) => ConversationRepositoryImpl(
    ConversationRemoteDataSource(
      ref.watch(httpClientProvider),
      canActOnPhone: ref.watch(phoneControlProvider).supported,
      deviceStatus: ref.watch(phoneControlProvider).status,
    ),
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

  static const Map<SpokenLanguage, String> _yesWords = {
    SpokenLanguage.uzbek: 'Ha',
    SpokenLanguage.tajik: 'Бале',
    SpokenLanguage.russian: 'Да',
    SpokenLanguage.english: 'Yes',
  };
  static const Map<SpokenLanguage, String> _noWords = {
    SpokenLanguage.uzbek: "Yo'q",
    SpokenLanguage.tajik: 'Не',
    SpokenLanguage.russian: 'Нет',
    SpokenLanguage.english: 'No',
  };
  static const Map<SpokenLanguage, String> _cancelled = {
    SpokenLanguage.uzbek: 'Mayli, bekor qildim.',
    SpokenLanguage.tajik: 'Хуб, бекор кардам.',
    SpokenLanguage.russian: 'Хорошо, отменил.',
    SpokenLanguage.english: 'Okay, I cancelled it.',
  };

  /// Calls and texts wait on the phone itself for the user's yes; this is
  /// the question's id, to tell it from the computer's.
  static const _phoneQuestionId = 'phone';
  static const Map<SpokenLanguage, String> _calling = {
    SpokenLanguage.uzbek: "Qo'ng'iroq qilyapman.",
    SpokenLanguage.tajik: 'Занг мезанам.',
    SpokenLanguage.russian: 'Звоню.',
    SpokenLanguage.english: 'Calling now.',
  };
  static const Map<SpokenLanguage, String> _sent = {
    SpokenLanguage.uzbek: 'Xabar yuborildi.',
    SpokenLanguage.tajik: 'Паём фиристода шуд.',
    SpokenLanguage.russian: 'Сообщение отправлено.',
    SpokenLanguage.english: 'Message sent.',
  };

  PhoneAction? _phoneAwaitingYes;

  @override
  ConversationState build() => const ConversationState();

  /// The action Sado is waiting for a yes on, if any.
  PendingAction? get pendingAction => state.lastReply?.pendingAction;

  /// Sends [text] to Sado and returns the reply, or `null` when Sado could
  /// not answer. While Sado waits for a yes, a short "yes" or "no" answers
  /// that question instead.
  Future<SadoReply?> ask(
    String text,
    SpokenLanguage language,
    SadoMode mode,
  ) {
    final repository = ref.read(conversationRepositoryProvider);
    final pending = pendingAction;
    if (pending != null) {
      switch (consentIn(text)) {
        case Consent.yes when pending.id == _phoneQuestionId:
          return _doOnPhone(text, language);
        case Consent.yes:
          return _send(
            text,
            language,
            (context) =>
                repository.confirmAction(pending.id, context, language, mode),
          );
        case Consent.no:
          return _cancel(pending, text, language);
        case Consent.unclear:
          break;
      }
    }
    return _send(
      text,
      language,
      (context) => ref.read(askSadoProvider).call(context, language, mode),
    );
  }

  /// Answers Sado's question from a Yes or No button.
  Future<SadoReply?> answer({
    required bool yes,
    required SpokenLanguage language,
    required SadoMode mode,
  }) => ask((yes ? _yesWords : _noWords)[language]!, language, mode);

  Future<SadoReply?> _send(
    String text,
    SpokenLanguage language,
    Future<Result<SadoReply>> Function(List<ChatMessage> context) request,
  ) async {
    final messages = [
      ...state.messages,
      ChatMessage(speaker: ChatSpeaker.user, text: text),
    ];
    state = ConversationState(messages: messages, isThinking: true);

    final context = messages.length > _contextSize
        ? messages.sublist(messages.length - _contextSize)
        : messages;
    final result = await request(context);

    switch (result) {
      case Ok(value: final answer):
        final value = await _actOnPhone(answer, language);
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

  /// Carries out what Sado asked the phone to do. If the phone could not,
  /// Sado says so instead of claiming it did.
  Future<SadoReply> _actOnPhone(
    SadoReply reply,
    SpokenLanguage language,
  ) async {
    final phone = ref.read(phoneControlProvider);
    var answer = reply;
    for (final action in reply.phoneActions) {
      if (action.needsYes) {
        _phoneAwaitingYes = action;
        answer = answer.asking(
          PendingAction(id: _phoneQuestionId, description: action.description),
        );
        continue;
      }
      final outcome = await phone.perform(action);
      final problem = phoneOutcomeMessage(outcome, action, language);
      if (problem != null) return reply.saying(problem);
    }
    return answer;
  }

  /// A call or a text the owner asked for at the computer: the phone asks
  /// here too, since it is the one that reaches the other person.
  void askOnPhone(PhoneAction action) {
    _phoneAwaitingYes = action;
    final question = SadoReply(
      text: '${action.description}?',
      pendingAction: PendingAction(
        id: _phoneQuestionId,
        description: action.description,
      ),
    );
    state = ConversationState(
      messages: [
        ...state.messages,
        ChatMessage(speaker: ChatSpeaker.sado, text: question.text),
      ],
      lastReply: question,
    );
  }

  /// The user said yes to a call or a text: the phone places or sends it.
  Future<SadoReply> _doOnPhone(String text, SpokenLanguage language) async {
    final action = _phoneAwaitingYes;
    _phoneAwaitingYes = null;
    final messages = [
      ...state.messages,
      ChatMessage(speaker: ChatSpeaker.user, text: text),
    ];
    state = ConversationState(messages: messages, isThinking: true);
    var said = _cancelled[language]!;
    if (action != null) {
      final outcome = await ref.read(phoneControlProvider).perform(action);
      said =
          phoneOutcomeMessage(outcome, action, language) ??
          (action.kind == 'call' ? _calling : _sent)[language]!;
    }
    final reply = SadoReply(text: said);
    state = ConversationState(
      messages: [
        ...messages,
        ChatMessage(speaker: ChatSpeaker.sado, text: said),
      ],
      lastReply: reply,
    );
    return reply;
  }

  Future<SadoReply> _cancel(
    PendingAction pending,
    String text,
    SpokenLanguage language,
  ) async {
    final reply = SadoReply(text: _cancelled[language]!);
    state = ConversationState(
      messages: [
        ...state.messages,
        ChatMessage(speaker: ChatSpeaker.user, text: text),
        ChatMessage(speaker: ChatSpeaker.sado, text: reply.text),
      ],
      lastReply: reply,
    );
    _phoneAwaitingYes = null;
    // Nothing runs without a yes anyway; telling the server only tidies up.
    if (pending.id != _phoneQuestionId) {
      await ref.read(conversationRepositoryProvider).cancelAction(pending.id);
    }
    return reply;
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
