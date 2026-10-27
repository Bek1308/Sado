import 'package:sado/core/error/result.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';
import 'package:sado/features/voices/domain/repositories/voice_repository.dart';

final class GetVoices {
  const GetVoices(this._repository);

  final VoiceRepository _repository;

  Future<Result<List<VoiceOption>>> call() => _repository.fetchVoices();
}
