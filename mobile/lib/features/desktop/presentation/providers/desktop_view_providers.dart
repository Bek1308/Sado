import 'package:flutter_riverpod/flutter_riverpod.dart';

/// How Sado shows itself on a computer: not at all, as a slim voice bar
/// while talking, or as the full conversation window.
enum DesktopView { hidden, compact, full }

final desktopViewProvider = NotifierProvider<DesktopViewSetting, DesktopView>(
  DesktopViewSetting.new,
);

class DesktopViewSetting extends Notifier<DesktopView> {
  @override
  DesktopView build() => DesktopView.hidden;

  DesktopView get current => state;
  set current(DesktopView view) => state = view;
}
