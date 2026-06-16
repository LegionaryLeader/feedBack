/*
 * fee[dB]ack v0.3.0 — Venue instrument POV resolver.
 *
 * Maps arrangement / instrument labels to venue background POVs.
 * Vocals/karaoke routing uses the active arrangement name only — not
 * lyrics overlay visibility during guitar practice.
 */
(function (root) {
    'use strict';

    const POV_IDS = Object.freeze(['guitar', 'bass', 'drums', 'piano', 'vocals']);

    function resolveVenueInstrumentPov(input) {
        const s = String(input == null ? '' : input).trim().toLowerCase();
        if (!s) return 'guitar';
        if (/\b(drums?)\b/.test(s)) return 'drums';
        if (/\b(bass)\b/.test(s)) return 'bass';
        if (/\b(piano|keys|keyboard)\b/.test(s)) return 'piano';
        if (/\b(karaoke|vocal|vocals|lyric|lyrics|sing|singing)\b/.test(s)) return 'vocals';
        if (/\b(lead|rhythm|guitar|combo)\b/.test(s)) return 'guitar';
        return 'guitar';
    }

    function isVocalsKaraokeArrangement(input) {
        return resolveVenueInstrumentPov(input) === 'vocals';
    }

    const api = {
        POV_IDS,
        resolveVenueInstrumentPov,
        isVocalsKaraokeArrangement,
    };

    if (root) root.v3VenueInstrumentPov = api;
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
}(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : null)));
