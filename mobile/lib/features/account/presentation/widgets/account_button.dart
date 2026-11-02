import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/core/router/app_router.dart';
import 'package:sado/features/account/presentation/providers/account_providers.dart';

/// Who is signed in, with a way to sign out; or a way to sign in.
class AccountButton extends ConsumerWidget {
  const AccountButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final account = ref.watch(accountProvider).value;
    if (account == null) {
      return IconButton(
        tooltip: 'Sign in',
        icon: const Icon(Icons.account_circle_outlined),
        onPressed: () => context.go(AppRoutes.signIn),
      );
    }
    final photo = account.photoUrl;
    return PopupMenuButton<void>(
      tooltip: account.email,
      icon: CircleAvatar(
        radius: 14,
        foregroundImage: photo == null ? null : NetworkImage(photo),
        child: Text(account.name.isEmpty ? '?' : account.name[0]),
      ),
      itemBuilder: (context) => [
        PopupMenuItem<void>(
          enabled: false,
          child: ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(account.name),
            subtitle: Text(account.email),
          ),
        ),
        const PopupMenuDivider(),
        PopupMenuItem<void>(
          onTap: () => ref.read(accountServiceProvider).signOut(),
          child: const ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(Icons.logout_rounded),
            title: Text('Sign out'),
          ),
        ),
      ],
    );
  }
}
