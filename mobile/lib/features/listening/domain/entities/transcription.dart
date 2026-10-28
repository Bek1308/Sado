import 'package:sado/features/speech/domain/entities/spoken_language.dart';

/// What was heard in a recording, with the language Sado detected.
typedef Transcription = ({String text, SpokenLanguage language});
