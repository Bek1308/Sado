import 'package:dio/dio.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class ConversationRemoteDataSource {
  const ConversationRemoteDataSource(this._httpClient);

  static const _repliesPath = '/replies';

  final Dio _httpClient;

  Future<SadoReply> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _repliesPath,
      data: {
        'language': language.code,
        'mode': mode.code,
        // Lets Sado read "tomorrow at 9" on the user's own clock.
        'utc_offset_minutes': DateTime.now().timeZoneOffset.inMinutes,
        'messages': [
          for (final message in conversation)
            {'speaker': message.speaker.code, 'text': message.text},
        ],
      },
    );
    final data = response.data!;
    return SadoReply(
      text: data['reply'] as String,
      // Older servers did not report what Sado remembered or set.
      remembered: [
        for (final fact in data['remembered'] as List<dynamic>? ?? const [])
          fact as String,
      ],
      reminded: [
        for (final reminder in data['reminded'] as List<dynamic>? ?? const [])
          reminder as String,
      ],
    );
  }
}
