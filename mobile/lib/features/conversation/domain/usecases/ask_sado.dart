import 'package:sado/core/error/result.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final class AskSado {
  const AskSado(this._repository);

  final ConversationRepository _repository;

  Future<Result<SadoReply>> call(
    List<ChatMessage> conversation,
    SpokenLanguage language,
  ) => _repository.reply(conversation, language);
}
