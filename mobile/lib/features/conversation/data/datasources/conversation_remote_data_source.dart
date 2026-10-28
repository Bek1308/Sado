import 'package:dio/dio.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class ConversationRemoteDataSource {
  const ConversationRemoteDataSource(this._httpClient);

  static const _repliesPath = '/replies';

  final Dio _httpClient;

  Future<String> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
  ) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _repliesPath,
      data: {
        'language': language.code,
        'messages': [
          for (final message in conversation)
            {'speaker': message.speaker.code, 'text': message.text},
        ],
      },
    );
    return response.data!['reply'] as String;
  }
}
