import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/core/router/app_router.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/features/account/presentation/providers/account_providers.dart';
import 'package:sado/features/conversation/presentation/widgets/sado_face.dart';

/// Asks once whether to sign in with Google. Signed in, Sado keeps a memory
/// of its own for this person and, on the owner's phone, reaches their
/// computer too.
class SignInPage extends ConsumerStatefulWidget {
  const SignInPage({super.key});

  @override
  ConsumerState<SignInPage> createState() => _SignInPageState();
}

class _SignInPageState extends ConsumerState<SignInPage> {
  bool _busy = false;
  String? _problem;

  Future<void> _signIn() async {
    setState(() {
      _busy = true;
      _problem = null;
    });
    try {
      final account = await ref.read(accountServiceProvider).signIn();
      if (account != null && mounted) context.go(AppRoutes.home);
    } on Exception {
      _problem = 'Could not sign in. Check the connection and try again.';
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _skip() async {
    await ref.read(accountSkippedProvider.notifier).skip();
    if (mounted) context.go(AppRoutes.home);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(
              maxWidth: AppLayout.maxContentWidth,
            ),
            child: LayoutBuilder(
              builder: (context, constraints) => SingleChildScrollView(
                padding: const EdgeInsets.all(AppSpacing.xl),
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minHeight: constraints.maxHeight - AppSpacing.xl * 2,
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SadoFace(size: 140),
                      const SizedBox(height: AppSpacing.xxl),
                      Text(
                        'Make Sado yours',
                        style: theme.textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      Text(
                        'Sign in with Google and Sado keeps your memories, '
                        'reminders and lists to you alone. With the same '
                        'account on your computer, each can reach the other.',
                        style: theme.textTheme.bodyLarge?.copyWith(
                          color: colors.onSurfaceVariant,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: AppSpacing.xxl),
                      SizedBox(
                        width: double.infinity,
                        height: 56,
                        child: FilledButton.icon(
                          onPressed: _busy ? null : _signIn,
                          icon: _busy
                              ? const SizedBox.square(
                                  dimension: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.account_circle_outlined),
                          label: const Text('Continue with Google'),
                        ),
                      ),
                      if (_problem case final problem?) ...[
                        const SizedBox(height: AppSpacing.md),
                        Text(
                          problem,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: colors.error,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                      const SizedBox(height: AppSpacing.sm),
                      TextButton(
                        onPressed: _busy ? null : _skip,
                        child: const Text('Try without an account'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
