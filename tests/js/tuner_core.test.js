'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const tunerCore = require('../../static/v3/tuner-core.js');

test('freqToNote maps A4 at 440 reference', () => {
    const n = tunerCore.freqToNote(440, 440);
    assert.strictEqual(n.name, 'A');
    assert.strictEqual(n.octave, 4);
    assert.strictEqual(n.cents, 0);
    assert.strictEqual(n.note, 'A4');
});

test('freqToNote maps middle C', () => {
    const n = tunerCore.freqToNote(261.63, 440);
    assert.strictEqual(n.note, 'C4');
    assert.ok(Math.abs(n.cents) <= 2);
});

test('freqToNote reports sharp/flat cents', () => {
    // A4 + 20 cents up.
    const sharp = tunerCore.freqToNote(440 * Math.pow(2, 20 / 1200), 440);
    assert.strictEqual(sharp.name, 'A');
    assert.ok(sharp.cents >= 18 && sharp.cents <= 22, 'cents ~+20, got ' + sharp.cents);
    const flat = tunerCore.freqToNote(440 * Math.pow(2, -20 / 1200), 440);
    assert.ok(flat.cents <= -18 && flat.cents >= -22, 'cents ~-20, got ' + flat.cents);
});

test('freqToNote honors a non-440 reference pitch', () => {
    // At A=442, a 442 Hz tone is exactly A4 (0 cents).
    const n = tunerCore.freqToNote(442, 442);
    assert.strictEqual(n.note, 'A4');
    assert.strictEqual(n.cents, 0);
});

test('freqToNote returns null for non-positive input', () => {
    assert.strictEqual(tunerCore.freqToNote(0, 440), null);
    assert.strictEqual(tunerCore.freqToNote(-5, 440), null);
});

test('yinDetect recovers the pitch of a synthetic sine', () => {
    const sampleRate = 44100;
    const freq = 220; // A3
    const n = 4096;
    const buf = new Float32Array(n);
    for (let i = 0; i < n; i++) buf[i] = Math.sin(2 * Math.PI * freq * i / sampleRate);
    const res = tunerCore.yinDetect(buf, sampleRate);
    assert.ok(Math.abs(res.frequency - freq) < 2, 'detected ' + res.frequency + ' Hz');
    assert.ok(res.confidence > 0.8, 'confidence ' + res.confidence);
    assert.strictEqual(tunerCore.freqToNote(res.frequency, 440).note, 'A3');
});

test('yinDetect returns zero for silence', () => {
    const res = tunerCore.yinDetect(new Float32Array(2048), 44100);
    assert.strictEqual(res.frequency, 0);
});
