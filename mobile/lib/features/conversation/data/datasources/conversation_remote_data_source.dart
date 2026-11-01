import 'package:dio/dio.dart';
import 'package:sado/features/conversation/domain/entities/chat_message.dart';
import 'package:sado/features/conversation/domain/entities/pending_action.dart';
import 'package:sado/features/conversation/domain/entities/sado_mode.dart';
import 'package:sado/features/conversation/domain/entities/sado_reply.dart';
import 'package:sado/features/phone/domain/entities/phone_action.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

class ConversationRemoteDataSource {
  const ConversationRemoteDataSource(
    this._httpClient, {
    this.canActOnPhone = false,
  });

  static const _repliesPath = '/replies';
  static const _actionsPath = '/actions';

  final Dio _httpClient;

  /// Whether this app can call, message or set alarms on the phone it runs
  /// on, so Sado may offer to.
  final bool canActOnPhone;

  Future<SadoReply> reply(
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) => _post(_repliesPath, conversation, language, mode);

  Future<SadoReply> confirmAction(
    String actionId,
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) => _post('$_actionsPath/$actionId/confirm', conversation, language, mode);

  Future<void> cancelAction(String actionId) =>
      _httpClient.post<void>('$_actionsPath/$actionId/cancel');

  Future<SadoReply> _post(
    String path,
    List<ChatMessage> conversation,
    SpokenLanguage language,
    SadoMode mode,
  ) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      path,
      data: {
        'language': language.code,
        'mode': mode.code,
        // Lets Sado read "tomorrow at 9" on the user's own clock.
        'utc_offset_minutes': DateTime.now().timeZoneOffset.inMinutes,
        'phone': canActOnPhone,
        'messages': [
          for (final message in conversation)
            {'speaker': message.speaker.code, 'text': message.text},
        ],
      },
    );
    return _reply(response.data!);
  }

  SadoReply _reply(Map<String, dynamic> data) {
    final pending = data['pending_action'] as Map<String, dynamic>?;
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
      listsChanged: data['lists_changed'] as bool? ?? false,
      pendingAction: pending == null
          ? null
          : PendingAction(
              id: pending['id'] as String,
              description: pending['description'] as String,
            ),
      phoneActions: [
        for (final action
            in data['phone_actions'] as List<dynamic>? ?? const [])
          PhoneAction(
            kind: (action as Map<String, dynamic>)['kind'] as String,
            details: (action['details'] as Map<String, dynamic>).map(
              (key, value) => MapEntry(key, value as String),
            ),
          ),
      ],
    );
  }
}
