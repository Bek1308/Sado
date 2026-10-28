enum SpokenLanguage {
  tajik(code: 'tg', nativeName: 'Тоҷикӣ'),
  uzbek(code: 'uz', nativeName: "O'zbekcha"),
  russian(code: 'ru', nativeName: 'Русский'),
  english(code: 'en', nativeName: 'English');

  const SpokenLanguage({required this.code, required this.nativeName});

  /// ISO 639-1 code shared with the server.
  final String code;
  final String nativeName;

  /// Parses a server language code; unknown codes fall back to Uzbek.
  static SpokenLanguage fromCode(String code) =>
      SpokenLanguage.values.firstWhere(
        (language) => language.code == code,
        orElse: () => SpokenLanguage.uzbek,
      );
}
