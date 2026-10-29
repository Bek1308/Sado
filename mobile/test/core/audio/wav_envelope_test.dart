import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:sado/core/audio/wav_envelope.dart';

const _rate = 1000;
const _frame = Duration(milliseconds: 100);

/// A mono 16-bit WAV of [samples], each from -1 to 1.
Uint8List _wav(List<double> samples, {int bitsPerSample = 16}) {
  final data = ByteData(samples.length * 2);
  for (var i = 0; i < samples.length; i++) {
    data.setInt16(i * 2, (samples[i] * 32767).round(), Endian.little);
  }
  final header = ByteData(44)
    ..setUint32(4, 36 + data.lengthInBytes, Endian.little)
    ..setUint32(16, 16, Endian.little)
    ..setUint16(20, 1, Endian.little)
    ..setUint16(22, 1, Endian.little)
    ..setUint32(24, _rate, Endian.little)
    ..setUint32(28, _rate * 2, Endian.little)
    ..setUint16(32, 2, Endian.little)
    ..setUint16(34, bitsPerSample, Endian.little)
    ..setUint32(40, data.lengthInBytes, Endian.little);
  final bytes = header.buffer.asUint8List()
    ..setAll(0, 'RIFF'.codeUnits)
    ..setAll(8, 'WAVE'.codeUnits)
    ..setAll(12, 'fmt '.codeUnits)
    ..setAll(36, 'data'.codeUnits);
  return Uint8List.fromList([...bytes, ...data.buffer.asUint8List()]);
}

List<double> _tone(int count, double volume) => [
  for (var i = 0; i < count; i++) volume * math.sin(i * 0.5),
];

void main() {
  test('rises on speech and falls in pauses', () {
    final wav = _wav([
      ..._tone(100, 0),
      ..._tone(100, 0.8),
      ..._tone(100, 0.2),
      ..._tone(100, 0),
    ]);

    final envelope = wavEnvelope(wav, frame: _frame);

    expect(envelope, hasLength(4));
    expect(envelope[0], 0);
    expect(envelope[1], closeTo(1, 0.01));
    expect(envelope[2], inExclusiveRange(0.3, 0.8));
    expect(envelope[3], 0);
  });

  test('does not blow a near-silent clip up into a shout', () {
    final envelope = wavEnvelope(_wav(_tone(100, 0.001)), frame: _frame);

    expect(envelope.single, lessThan(0.3));
  });

  test('gives no envelope for audio it cannot read', () {
    expect(wavEnvelope(Uint8List.fromList([1, 2, 3]), frame: _frame), isEmpty);
    expect(
      wavEnvelope(_wav(_tone(100, 0.5), bitsPerSample: 8), frame: _frame),
      isEmpty,
    );
  });
}
