'use strict';

/**
 * WAV fixture integration tests for the YIN pitch detector.
 *
 * Drop any 16-bit PCM WAV file named <Note><Octave>_<FreqHz>Hz.wav into
 * tests/plugins/tuner/fixtures/audio/ and it is automatically picked up and tested.
 *
 * Examples:
 *   A4_440.0Hz.wav   →  expected 440.0 Hz
 *   E2_82.41Hz.wav   →  expected 82.41 Hz
 *   D3_146.83Hz.wav  →  expected 146.83 Hz
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { _yinDetect } = require('../../../../plugins/tuner/workers/yin.js');
const { parseWav } = require('./helpers/wav-parser.js');

const FIXTURES_DIR = path.join(__dirname, '../fixtures/audio');
const WAV_NAME_RE = /^([A-G]#?[0-9])_([\d.]+)Hz[^.]*\.wav$/i;
const MIN_FRAME = 4096;
// 2% tolerance ≈ 35 cents — generous enough for real recordings, tight enough
// to catch octave errors or misidentified notes.
const TOLERANCE_PCT = 2;

const wavFiles = fs.readdirSync(FIXTURES_DIR).filter(f => WAV_NAME_RE.test(f));

if (wavFiles.length === 0) {
    test('WAV fixtures', {
        skip: 'No WAV fixtures found in tests/plugins/tuner/fixtures/audio/ — run: python tests/plugins/tuner/fixtures/generate_audio.py'
    }, () => {});
} else {
    for (const filename of wavFiles) {
        const [, note, freqStr] = filename.match(WAV_NAME_RE);
        const expectedHz = parseFloat(freqStr);

        test(`WAV ${filename}: detects ${expectedHz} Hz (${note})`, () => {
            const fileBuffer = fs.readFileSync(path.join(FIXTURES_DIR, filename));
            const { samples, sampleRate } = parseWav(fileBuffer);

            assert.ok(
                samples.length >= MIN_FRAME,
                `WAV too short: need ≥${MIN_FRAME} samples, got ${samples.length}`
            );

            // Take MIN_FRAME samples from the middle of the file to avoid
            // attack/release transients at the edges.
            const mid = Math.floor(samples.length / 2);
            const start = Math.max(0, mid - MIN_FRAME / 2);
            const frame = samples.slice(start, start + MIN_FRAME);

            const result = _yinDetect(frame, sampleRate);
            assert.ok(result.freq > 0, `No pitch detected for ${filename} (rms=${result.rms.toFixed(4)})`);

            const errorPct = Math.abs(result.freq - expectedHz) / expectedHz * 100;
            assert.ok(
                errorPct < TOLERANCE_PCT,
                `${filename}: expected ${expectedHz} Hz ±${TOLERANCE_PCT}%, got ${result.freq.toFixed(2)} Hz (error ${errorPct.toFixed(2)}%)`
            );
        });
    }
}
