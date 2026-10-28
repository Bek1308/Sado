import 'package:sado/core/camera/photo_picker.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';

abstract interface class ExplanationRepository {
  /// Reads the photographed paper and explains it in [language].
  Future<Result<String>> explain(
    Photograph photo,
    SpokenLanguage language,
  );
}
