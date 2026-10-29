import 'package:flutter_test/flutter_test.dart';
import 'package:sado/features/speech/domain/entities/spoken_chunks.dart';

void main() {
  test('splits a reply into sentences', () {
    expect(
      spokenChunks(
        'Bugun havo ochiq va iliq. Kechqurun 8 darajagacha soviydi! '
        'Soyabon olish shart emas.',
      ),
      [
        'Bugun havo ochiq va iliq.',
        'Kechqurun 8 darajagacha soviydi!',
        'Soyabon olish shart emas.',
      ],
    );
  });

  test('keeps very short sentences with their neighbours', () {
    expect(spokenChunks('Ha. Albatta. Ertaga soat 9 da eslataman.'), [
      'Ha. Albatta. Ertaga soat 9 da eslataman.',
    ]);
    expect(spokenChunks('Ertaga soat 9 da eslataman. Xo‘p.'), [
      'Ertaga soat 9 da eslataman. Xo‘p.',
    ]);
  });

  test('does not split decimals or leave blanks', () {
    expect(spokenChunks('  Kurs 9.22 somoni.  '), ['Kurs 9.22 somoni.']);
    expect(spokenChunks('   '), isEmpty);
  });
}
