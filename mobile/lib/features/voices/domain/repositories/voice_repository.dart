import 'package:sado/core/error/result.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';

abstract interface class VoiceRepository {
  Future<Result<List<VoiceOption>>> fetchVoices();
}
