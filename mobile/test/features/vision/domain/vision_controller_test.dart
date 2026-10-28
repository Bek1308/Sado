import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/camera/photo_picker.dart';
import 'package:sado/core/error/failure.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/features/speech/domain/entities/spoken_language.dart';
import 'package:sado/features/vision/domain/repositories/explanation_repository.dart';
import 'package:sado/features/vision/presentation/providers/vision_providers.dart';

const _photo = Photograph(path: '/tmp/notice.jpg', mimeType: 'image/jpeg');

final class _FakePicker implements PhotoPicker {
  _FakePicker({this.photo = _photo, this.denied = false});

  final Photograph? photo;
  final bool denied;

  @override
  Future<Photograph?> takePhoto() async {
    if (denied) throw Exception('camera denied');
    return photo;
  }
}

final class _FakeRepository implements ExplanationRepository {
  _FakeRepository(this.result);

  final Result<String> result;
  SpokenLanguage? askedLanguage;

  @override
  Future<Result<String>> explain(
    Photograph photo,
    SpokenLanguage language,
  ) async {
    askedLanguage = language;
    return result;
  }
}

ProviderContainer _container(
  _FakePicker picker,
  _FakeRepository repository,
) {
  final container = ProviderContainer(
    overrides: [
      photoPickerProvider.overrideWithValue(picker),
      explanationRepositoryProvider.overrideWithValue(repository),
    ],
  );
  addTearDown(container.dispose);
  return container;
}

void main() {
  test('explains the photographed paper in the current language', () async {
    final repository = _FakeRepository(const Ok('This is a notice.'));
    final container = _container(_FakePicker(), repository);
    final controller = container.read(visionControllerProvider.notifier);

    await controller.explain();

    expect(
      container.read(visionControllerProvider),
      isA<VisionExplained>().having(
        (explained) => explained.text,
        'text',
        'This is a notice.',
      ),
    );
    expect(repository.askedLanguage, SpokenLanguage.uzbek);
  });

  test('stays idle when the user cancels the camera', () async {
    final container = _container(
      _FakePicker(photo: null),
      _FakeRepository(const Ok('')),
    );

    await container.read(visionControllerProvider.notifier).explain();

    expect(container.read(visionControllerProvider), isA<VisionIdle>());
  });

  test('reports a camera that cannot be opened', () async {
    final container = _container(
      _FakePicker(denied: true),
      _FakeRepository(const Ok('')),
    );

    await container.read(visionControllerProvider.notifier).explain();

    expect(container.read(visionControllerProvider), isA<VisionFailed>());
  });

  test('reports a failed explanation', () async {
    final container = _container(
      _FakePicker(),
      _FakeRepository(
        const Err(ServerFailure('Sado cannot think right now')),
      ),
    );

    await container.read(visionControllerProvider.notifier).explain();

    expect(
      container.read(visionControllerProvider),
      isA<VisionFailed>().having(
        (failed) => failed.message,
        'message',
        'Sado cannot think right now',
      ),
    );
  });
}
