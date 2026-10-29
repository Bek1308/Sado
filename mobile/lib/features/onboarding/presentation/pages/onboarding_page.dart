import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sado/core/router/app_router.dart';
import 'package:sado/core/theme/app_spacing.dart';
import 'package:sado/core/theme/app_theme.dart';
import 'package:sado/features/conversation/presentation/widgets/sado_face.dart';
import 'package:sado/features/onboarding/presentation/providers/onboarding_providers.dart';

/// A three-page introduction shown once, before the first conversation.
class OnboardingPage extends ConsumerStatefulWidget {
  const OnboardingPage({super.key});

  @override
  ConsumerState<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends ConsumerState<OnboardingPage> {
  static const _pageTurn = Duration(milliseconds: 350);

  final _pages = PageController();
  int _index = 0;

  static const _slides = [
    _Slide(
      art: SadoFace(size: 160),
      title: 'Talk in your own language',
      body:
          'Tajik, Uzbek, Russian or English. Just speak — Sado works out '
          'which language you used and answers in it.',
    ),
    _Slide(
      art: _IconArt(Icons.auto_awesome_rounded),
      title: 'Sado remembers and acts',
      body:
          'It keeps the facts you share, sets reminders, manages your lists '
          'and checks the web for weather, news and prices.',
    ),
    _Slide(
      art: _IconArt(Icons.document_scanner_outlined),
      title: 'Any paper, explained',
      body:
          'Photograph a letter or share a PDF. Sado tells you what it is, '
          'what it asks of you and by when.',
    ),
  ];

  bool get _onLastPage => _index == _slides.length - 1;

  @override
  void dispose() {
    _pages.dispose();
    super.dispose();
  }

  Future<void> _finish() async {
    await ref.read(onboardingDoneProvider.notifier).finish();
    if (mounted) context.go(AppRoutes.home);
  }

  Future<void> _next() => _onLastPage
      ? _finish()
      : _pages.nextPage(duration: _pageTurn, curve: Curves.easeOutCubic);

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(
              maxWidth: AppLayout.maxContentWidth,
            ),
            child: Column(
              children: [
                Align(
                  alignment: Alignment.centerRight,
                  child: Padding(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    child: AnimatedOpacity(
                      opacity: _onLastPage ? 0 : 1,
                      duration: _pageTurn,
                      child: TextButton(
                        onPressed: _onLastPage ? null : _finish,
                        child: const Text('Skip'),
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: PageView(
                    controller: _pages,
                    onPageChanged: (index) => setState(() => _index = index),
                    children: _slides,
                  ),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  spacing: AppSpacing.sm,
                  children: [
                    for (var dot = 0; dot < _slides.length; dot++)
                      AnimatedContainer(
                        duration: _pageTurn,
                        width: dot == _index ? 24 : 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: dot == _index
                              ? colors.primary
                              : colors.outlineVariant,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                  ],
                ),
                Padding(
                  padding: const EdgeInsets.all(AppSpacing.xl),
                  child: SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: FilledButton(
                      onPressed: _next,
                      child: Text(_onLastPage ? 'Start talking' : 'Next'),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Slide extends StatelessWidget {
  const _Slide({required this.art, required this.title, required this.body});

  final Widget art;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xxl),
      child: Column(
        children: [
          const SizedBox(height: AppSpacing.xxl),
          SizedBox(height: 180, child: Center(child: art)),
          const SizedBox(height: AppSpacing.xxl),
          Text(
            title,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            body,
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

/// A brand-coloured disc carrying one icon, matching Sado's orb.
class _IconArt extends StatelessWidget {
  const _IconArt(this.icon);

  final IconData icon;

  static const _size = 140.0;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: _size,
      height: _size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: AppTheme.brandGradient,
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.brandGradient[1].withValues(alpha: 0.3),
            blurRadius: _size / 3,
            spreadRadius: _size / 12,
          ),
        ],
      ),
      child: Icon(icon, size: _size / 2.2, color: Colors.white),
    );
  }
}
