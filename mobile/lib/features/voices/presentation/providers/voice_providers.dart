import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/voices/data/datasources/voice_remote_data_source.dart';
import 'package:sado/features/voices/data/repositories/voice_repository_impl.dart';
import 'package:sado/features/voices/domain/entities/voice_option.dart';
import 'package:sado/features/voices/domain/repositories/voice_repository.dart';
import 'package:sado/features/voices/domain/usecases/get_voices.dart';

final voiceRepositoryProvider = Provider<VoiceRepository>(
  (ref) => VoiceRepositoryImpl(
    VoiceRemoteDataSource(ref.watch(httpClientProvider)),
  ),
);

final getVoicesProvider = Provider<GetVoices>(
  (ref) => GetVoices(ref.watch(voiceRepositoryProvider)),
);

final voicesProvider = FutureProvider<Result<List<VoiceOption>>>(
  (ref) => ref.watch(getVoicesProvider).call(),
);

/// The voice the user picked; `null` means the server's default voice.
final selectedVoiceIdProvider = NotifierProvider<SelectedVoiceId, String?>(
  SelectedVoiceId.new,
);

class SelectedVoiceId extends Notifier<String?> {
  @override
  String? build() => null;

  String? get selected => state;
  set selected(String? voiceId) => state = voiceId;
}
