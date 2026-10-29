import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/error/result.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/lists/data/datasources/list_remote_data_source.dart';
import 'package:sado/features/lists/data/repositories/list_repository_impl.dart';
import 'package:sado/features/lists/domain/entities/sado_list.dart';
import 'package:sado/features/lists/domain/repositories/list_repository.dart';
import 'package:sado/features/lists/domain/usecases/cross_off.dart';
import 'package:sado/features/lists/domain/usecases/get_lists.dart';

final listRepositoryProvider = Provider<ListRepository>(
  (ref) =>
      ListRepositoryImpl(ListRemoteDataSource(ref.watch(httpClientProvider))),
);

final listsControllerProvider =
    AsyncNotifierProvider<ListsController, List<SadoList>>(
      ListsController.new,
    );

class ListsController extends AsyncNotifier<List<SadoList>> {
  ListRepository get _repository => ref.read(listRepositoryProvider);

  @override
  Future<List<SadoList>> build() async {
    final result = await GetLists(_repository).call();
    return switch (result) {
      Ok(:final value) => value,
      Err(:final failure) => throw failure,
    };
  }

  /// Crosses [entry] off at once and puts it back if the server refuses.
  /// Returns why it could not be crossed off, or `null` on success.
  Future<String?> crossOff(ListEntry entry) async {
    final before = state.value ?? const <SadoList>[];
    state = AsyncData([
      for (final list in before)
        if (list.entries.any((kept) => kept.id != entry.id))
          SadoList(
            name: list.name,
            entries: [
              for (final kept in list.entries)
                if (kept.id != entry.id) kept,
            ],
          ),
    ]);

    final result = await CrossOff(_repository).call(entry.id);
    if (result case Err(:final failure)) {
      state = AsyncData(before);
      return failure.message;
    }
    return null;
  }
}
