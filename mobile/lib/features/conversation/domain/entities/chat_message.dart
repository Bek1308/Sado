enum ChatSpeaker {
  user(code: 'user'),
  sado(code: 'sado');

  const ChatSpeaker({required this.code});

  /// Identifier shared with the server.
  final String code;
}

final class ChatMessage {
  const ChatMessage({required this.speaker, required this.text});

  final ChatSpeaker speaker;
  final String text;
}
