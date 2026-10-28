import 'package:sado/core/camera/photo_picker.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/vision/domain/repositories/explanation_repository.dart';

final class ExplainPhotograph {
  const ExplainPhotograph(this._repository);

  final ExplanationRepository _repository;

  Future<Result<String>> call(
    Photograph photo,
    SpokenLanguage language,
  ) => _repository.explain(photo, language);
}
