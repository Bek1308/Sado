import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sado/app.dart';
import 'package:sado/core/desktop/desktop_host.dart';
import 'package:sado/core/storage/preferences.dart';
import 'package:sado/features/account/presentation/providers/account_providers.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (DesktopHost.supported) await DesktopHost.prepare();
  // Android reads the project from google-services.json.
  if (accountsSupported) await Firebase.initializeApp();
  final preferences = await SharedPreferences.getInstance();
  runApp(
    ProviderScope(
      overrides: [sharedPreferencesProvider.overrideWithValue(preferences)],
      child: const SadoApp(),
    ),
  );
}
