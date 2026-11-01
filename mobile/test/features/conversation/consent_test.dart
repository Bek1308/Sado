import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/conversation/domain/entities/consent.dart';

void main() {
  test('hears yes in every language', () {
    for (final answer in [
      'Ha',
      'Ha, qil!',
      'Бале',
      'Да, давай',
      'Yes please',
    ]) {
      expect(consentIn(answer), Consent.yes, reason: answer);
    }
  });

  test('hears no, whichever apostrophe the recognizer used', () {
    for (final answer in [
      "Yo'q",
      'Yoʻq',
      'Yo‘q, kerak emas',
      'Нет',
      'Не',
      'No',
    ]) {
      expect(consentIn(answer), Consent.no, reason: answer);
    }
  });

  test('treats a longer sentence as a new request, not an answer', () {
    expect(
      consentIn('Ha, lekin avval ob-havoni ayt va keyin yoz'),
      Consent.unclear,
    );
    expect(consentIn('Havo qanday?'), Consent.unclear);
    expect(consentIn(''), Consent.unclear);
  });
}
