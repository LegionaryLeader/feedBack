/*
 * fee[dB]ack v0.3.0 — shared tuner DSP/math.
 *
 * A small, dependency-free YIN pitch detector + frequency→note/cents helper,
 * used by the topbar tuner badge (and reusable by anything else that needs a
 * lightweight readout). This intentionally does NOT reach into the external
 * note_detect plugin's internals — it's a standalone copy of the standard
 * algorithm (constitution P-II, plugin isolation). Browser-global as
 * `window.tunerCore`; also CommonJS-exported for node tests (tests/js).
 */
(function (root) {
    'use strict';

    const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

    /**
     * YIN pitch detection on a Float32 time-domain buffer.
     * @returns {{frequency:number, confidence:number}} frequency in Hz (0 if
     *          none found), confidence in 0..1 (1 - aperiodicity).
     */
    function yinDetect(buffer, sampleRate, threshold) {
        threshold = threshold == null ? 0.12 : threshold;
        const n = buffer.length;
        const halfN = Math.floor(n / 2);
        const yin = new Float32Array(halfN);

        // Difference function.
        for (let tau = 0; tau < halfN; tau++) {
            let sum = 0;
            for (let i = 0; i < halfN; i++) {
                const delta = buffer[i] - buffer[i + tau];
                sum += delta * delta;
            }
            yin[tau] = sum;
        }

        // Cumulative mean normalized difference.
        yin[0] = 1;
        let running = 0;
        for (let tau = 1; tau < halfN; tau++) {
            running += yin[tau];
            yin[tau] = running > 0 ? yin[tau] * tau / running : 1;
        }

        // Absolute threshold: first dip below `threshold`, then the local min.
        let tauEstimate = -1;
        for (let tau = 2; tau < halfN; tau++) {
            if (yin[tau] < threshold) {
                while (tau + 1 < halfN && yin[tau + 1] < yin[tau]) tau++;
                tauEstimate = tau;
                break;
            }
        }
        if (tauEstimate === -1) return { frequency: 0, confidence: 0 };

        // Parabolic interpolation around the dip for sub-sample accuracy.
        const x0 = tauEstimate > 0 ? tauEstimate - 1 : tauEstimate;
        const x2 = tauEstimate + 1 < halfN ? tauEstimate + 1 : tauEstimate;
        let betterTau = tauEstimate;
        if (x0 !== tauEstimate && x2 !== tauEstimate) {
            const s0 = yin[x0], s1 = yin[tauEstimate], s2 = yin[x2];
            const denom = 2 * (2 * s1 - s2 - s0);
            if (denom !== 0) betterTau = tauEstimate + (s2 - s0) / denom;
        }
        // A near-zero denom can fling betterTau out of [x0, x2] or non-finite,
        // making frequency Infinity/NaN; clamp it back to the dip neighbourhood
        // and treat a non-positive tau as "no detection" (frequency 0).
        if (!Number.isFinite(betterTau) || betterTau < x0 || betterTau > x2) betterTau = tauEstimate;
        return {
            frequency: betterTau > 0 ? sampleRate / betterTau : 0,
            confidence: Math.max(0, Math.min(1, 1 - yin[tauEstimate])),
        };
    }

    /**
     * Map a frequency to the nearest note + cents deviation.
     * @param {number} freq Hz
     * @param {number} [referencePitch=440] A4 reference (430–450)
     * @returns {{name,octave,note,midi,cents,targetFreq}|null}
     */
    function freqToNote(freq, referencePitch) {
        if (!freq || freq <= 0) return null;
        const a4 = referencePitch || 440;
        const midiFloat = 69 + 12 * Math.log2(freq / a4);
        const midi = Math.round(midiFloat);
        const targetFreq = a4 * Math.pow(2, (midi - 69) / 12);
        const cents = Math.round(1200 * Math.log2(freq / targetFreq));
        const name = NOTE_NAMES[((midi % 12) + 12) % 12];
        const octave = Math.floor(midi / 12) - 1;
        return { name, octave, note: name + octave, midi, cents, targetFreq };
    }

    const api = { yinDetect, freqToNote, NOTE_NAMES };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.tunerCore = api;
})(typeof window !== 'undefined' ? window : null);
