import 'package:dio/dio.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/dio_failure.dart';
import 'package:sado/features/conversation/data/datasources/conversation_remote_data_source.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/conversation/domain/repositories/conversation_repository.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

final class ConversationRepositoryImpl implements ConversationRepository {
  const ConversationRepositoryImpl(this._remoteDataSource);

  final ConversationRemoteDataSource _remoteDataSource;

  @override
  Future<Result<SadoReply>> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) {
    return _guard(
      () => _remoteDataSource.reply(conversation, language, mode),
    );
  }

  @override
  Future<Result<SadoReply>> confirmAction(
    String actionId,
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) => _guard(
    () => _remoteDataSource.confirmAction(
      actionId,
      conversation,
      language,
      mode,
    ),
  );

  @override
  Future<Result<void>> cancelAction(String actionId) =>
      _guard(() => _remoteDataSource.cancelAction(actionId));

  Future<Result<T>> _guard<T>(Future<T> Function() request) async {
    try {
      return Ok(await request());
    } on DioException catch (error) {
      return Err(error.toFailure());
    }
  }
}
