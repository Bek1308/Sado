import 'dart:math' as math;
import 'dart:typed_data';

/// How loud a WAV clip is over time, as values from 0 (silence) to 1 (its
/// loudest moment), one per [frame].
///
/// Sado's mouth follows this while the clip plays, so it opens on syllables
/// and closes in pauses. Only 16-bit PCM, the format the server sends, is
/// read; anything else gives an empty envelope and a still mouth.
List<double> wavEnvelope(Uint8List wav, {required Duration frame}) {
  final format = _Format.read(wav);
  if (format == null) return const [];
  final samplesPerFrame = math.max(
    1,
    format.sampleRate * frame.inMicroseconds ~/ Duration.microsecondsPerSecond,
  );
  final data = ByteData.sublistView(wav, format.dataStart, format.dataEnd);
  final sampleCount = data.lengthInBytes ~/ (2 * format.channels);
  final levels = <double>[];
  for (var start = 0; start < sampleCount; start += samplesPerFrame) {
    final end = math.min(start + samplesPerFrame, sampleCount);
    var sumOfSquares = 0.0;
    for (var sample = start; sample < end; sample++) {
      final value =
          data.getInt16(sample * 2 * format.channels, Endian.little) / 32768;
      sumOfSquares += value * value;
    }
    levels.add(math.sqrt(sumOfSquares / (end - start)));
  }
  final loudest = levels.fold<double>(0, math.max);
  // A floor keeps near-silent clips from being stretched into full shouts.
  final scale = math.max(loudest, 0.05);
  // The square root follows how loud speech feels rather than its energy.
  return [for (final level in levels) math.sqrt(level / scale).clamp(0, 1)];
}

final class _Format {
  const _Format(this.sampleRate, this.channels, this.dataStart, this.dataEnd);

  final int sampleRate;
  final int channels;
  final int dataStart;
  final int dataEnd;

  static _Format? read(Uint8List wav) {
    const headerLength = 12;
    if (wav.length < headerLength ||
        String.fromCharCodes(wav, 0, 4) != 'RIFF' ||
        String.fromCharCodes(wav, 8, 12) != 'WAVE') {
      return null;
    }
    final bytes = ByteData.sublistView(wav);
    int? sampleRate;
    int? channels;
    int? bitsPerSample;
    var offset = headerLength;
    while (offset + 8 <= wav.length) {
      final id = String.fromCharCodes(wav, offset, offset + 4);
      final size = bytes.getUint32(offset + 4, Endian.little);
      final body = offset + 8;
      if (id == 'fmt ' && body + 16 <= wav.length) {
        channels = bytes.getUint16(body + 2, Endian.little);
        sampleRate = bytes.getUint32(body + 4, Endian.little);
        bitsPerSample = bytes.getUint16(body + 14, Endian.little);
      } else if (id == 'data') {
        if (sampleRate == null || channels == null || bitsPerSample != 16) {
          return null;
        }
        return _Format(
          sampleRate,
          channels,
          body,
          math.min(body + size, wav.length),
        );
      }
      // Chunks are padded to an even number of bytes.
      offset = body + size + (size.isOdd ? 1 : 0);
    }
    return null;
  }
}
