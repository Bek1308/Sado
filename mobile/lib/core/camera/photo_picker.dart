import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

final photoPickerProvider = Provider<PhotoPicker>(
  (_) => const ImagePickerPhotoPicker(),
);

final class Photograph {
  const Photograph({required this.path, required this.mimeType});

  final String path;
  final String mimeType;
}

abstract interface class PhotoPicker {
  /// Captures a photo with the camera, or returns `null` when the user
  /// cancels.
  Future<Photograph?> takePhoto();
}

final class ImagePickerPhotoPicker implements PhotoPicker {
  const ImagePickerPhotoPicker();

  @override
  Future<Photograph?> takePhoto() async {
    final photo = await ImagePicker().pickImage(
      source: ImageSource.camera,
      // Enough to read small print, small enough to upload quickly over
      // mobile data.
      maxWidth: 2048,
      maxHeight: 2048,
      imageQuality: 85,
    );
    if (photo == null) return null;
    return Photograph(
      path: photo.path,
      mimeType: photo.mimeType ?? 'image/jpeg',
    );
  }
}
