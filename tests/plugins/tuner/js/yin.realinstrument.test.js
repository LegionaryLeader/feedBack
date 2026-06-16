'use strict';

/**
 * Real-instrument WAV fixture tests for the YIN pitch detector.
 *
 * Drop a 16-bit PCM WAV recording (mono or stereo) named
 * <NoteClass><Octave>_<FreqHz>Hz.wav into tests/plugins/tuner/fixtures/audio/real/
 * and it is automatically picked up and tested.
 *
 * Examples:
 *   E2_82.41Hz.wav   →  expected 82.41 Hz  (open low-E on guitar)
 *   A#3_233.08Hz.wav →  expected 233.08 Hz (A#3)
 *
 * Tolerance: ±20 cents (computed as 1200 * |log2(detected / expected)|).
 * This is tighter than the synthetic-fixture suite (≈34 cents at 2%) to
 * surface real-world detection regressions.
 *
 * See tests/plugins/tuner/fixtures/audio/real/README.md for recording guidelines.
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { _yinDetect } = require('../../../../plugins/tuner/workers/yin.js');
const { parseWav } = require('./helpers/wav-parser.js');

const FIXTURES_DIR = path.join(__dirname, '../fixtures/audio/real');
const WAV_NAME_RE = /^([A-G]#?[0-9])_([\d.]+)Hz[^.]*\.wav$/i;
const MIN_FRAME = 4096;
const TOLERANCE_CENTS = 20;

const wavFiles = fs.readdirSync(FIXTURES_DIR).filter(f => WAV_NAME_RE.test(f));

if (wavFiles.length === 0) {
    test('Real-instrument WAV fixtures', {
        skip: 'No real-instrument WAV fixtures found in tests/plugins/tuner/fixtures/audio/real/ — record a note and name it e.g. E2_82.41Hz.wav'
    }, () => {});
} else {
    for (const filename of wavFiles) {
        const [, note, freqStr] = filename.match(WAV_NAME_RE);
        const expectedHz = parseFloat(freqStr);

        test(`Real WAV ${filename}: detects ${freqStr} Hz (${note})`, () => {
            const fileBuffer = fs.readFileSync(path.join(FIXTURES_DIR, filename));
            const { samples, sampleRate } = parseWav(fileBuffer);

            assert.ok(
                samples.length >= MIN_FRAME,
                `WAV too short: need ≥${MIN_FRAME} samples, got ${samples.length}`
            );

            // Extract MIN_FRAME samples from the middle to skip attack/release transients.
            const mid = Math.floor(samples.length / 2);
            const start = Math.max(0, mid - MIN_FRAME / 2);
            const frame = samples.slice(start, start + MIN_FRAME);

            const result = _yinDetect(frame, sampleRate);
            assert.ok(result.freq > 0, `No pitch detected for ${filename} (rms=${result.rms.toFixed(4)})`);

            const centsError = 1200 * Math.abs(Math.log2(result.freq / expectedHz));
            assert.ok(
                centsError <= TOLERANCE_CENTS,
                `${filename}: expected ${expectedHz} Hz, got ${result.freq.toFixed(2)} Hz (${centsError.toFixed(1)} cents off — limit ${TOLERANCE_CENTS} cents)`
            );
        });
    }
}
