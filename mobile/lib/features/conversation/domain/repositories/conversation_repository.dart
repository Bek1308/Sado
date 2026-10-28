import 'package:sado/core/error/result.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

abstract interface class ConversationRepository {
  /// Returns Sado's answer to the last user message of [conversation].
  Future<Result<SadoReply>> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
  );
}
