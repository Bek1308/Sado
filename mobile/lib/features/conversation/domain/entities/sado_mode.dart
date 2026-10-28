enum SadoMode {
  home(code: 'home', label: 'Home'),
  personal(code: 'personal', label: 'Personal'),
  work(code: 'work', label: 'Work'),
  onTheGo(code: 'on_the_go', label: 'On the go');

  const SadoMode({required this.code, required this.label});

  /// Identifier shared with the server.
  final String code;
  final String label;
}
