import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/core/network/http_client.dart';
import 'package:sado/features/account/presentation/providers/account_providers.dart';
import 'package:sado/features/conversation/presentation/providers/conversation_providers.dart';
import 'package:sado/features/conversation/presentation/providers/live_providers.dart';
import 'package:sado/features/phone/domain/entities/phone_action.dart';
import 'package:sado/features/phone/presentation/providers/phone_providers.dart';

/// Carries out what the owner asked for at their computer, e.g. "set an alarm
/// on my phone", while Sado is open on the phone. Also starts listening at
/// once when Sado was opened to talk: from the assist button, the quick
/// settings tile or the app shortcut.
class PhoneInboxListener extends ConsumerStatefulWidget {
  const PhoneInboxListener({required this.child, super.key});

  final Widget child;

  @override
  ConsumerState<PhoneInboxListener> createState() => _PhoneInboxListenerState();
}

class _PhoneInboxListenerState extends ConsumerState<PhoneInboxListener>
    with WidgetsBindingObserver {
  static const _every = Duration(seconds: 4);
  static const _launch = MethodChannel('sado/launch');

  Timer? _timer;
  bool _checking = false;

  /// Only the owner's phone has an inbox; anyone else stops asking.
  bool _notTheOwner = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _timer = Timer.periodic(_every, (_) => unawaited(_check()));
    unawaited(_talkIfAsked());
  }

  Future<void> _talkIfAsked() async {
    final asked = await _launch.invokeMethod<bool>('takeTalkRequest') ?? false;
    final live = ref.read(liveConversationProvider);
    if (asked && mounted && !live.isLive) {
      await ref.read(liveConversationProvider.notifier).start();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Android lets an app open the dialer or the clock only while it is in
    // front, so the inbox is read while Sado is open.
    if (state == AppLifecycleState.resumed) {
      unawaited(_check());
      unawaited(_talkIfAsked());
    }
  }

  Future<void> _check() async {
    final resumed =
        WidgetsBinding.instance.lifecycleState == AppLifecycleState.resumed;
    final signedIn = ref.read(accountServiceProvider).current != null;
    if (_checking || _notTheOwner || !resumed || !signedIn) return;
    _checking = true;
    try {
      final response = await ref
          .read(httpClientProvider)
          .get<List<dynamic>>('/phone/actions');
      final phone = ref.read(phoneControlProvider);
      for (final item in response.data ?? const []) {
        final fields = item as Map<String, dynamic>;
        final action = PhoneAction(
          kind: fields['kind'] as String,
          details: (fields['details'] as Map<String, dynamic>).map(
            (key, value) => MapEntry(key, value as String),
          ),
        );
        if (action.needsYes) {
          ref.read(conversationControllerProvider.notifier).askOnPhone(action);
        } else {
          await phone.perform(action);
        }
      }
    } on DioException catch (error) {
      _notTheOwner = error.response?.statusCode == 403;
    } finally {
      _checking = false;
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // A new sign-in may be the owner's.
    ref.listen(accountProvider, (_, _) => _notTheOwner = false);
    return widget.child;
  }
}
