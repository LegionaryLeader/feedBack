// Core tuning capability domain.
(function () {
    'use strict';

    window.slopsmith = window.slopsmith || {};
    const capabilities = window.slopsmith.capabilities;
    if (!capabilities || capabilities.version !== 1) return;
    if (window.slopsmith.tunings && window.slopsmith.tunings.version === 1) return;

    capabilities.registerOwner('tuning', {
        description: 'Provides merged guitar/bass tunings from core defaults and plugin contributors.',
        operations: ['get-tunings'],
        events: ['tunings-updated'],
        kind: 'command',
        ownership: 'exclusive-owner',
    });

    // v3 instruments badge panel reads /api/tunings to populate its dropdowns
    // and re-renders when the tuner emits tunings-updated.
    capabilities.registerParticipant('core.settings.instruments', {
        tuning: {
            roles: ['requester'],
            operations: ['get-tunings'],
            events: ['tunings-updated'],
            mode: 'active',
            compatibility: 'none',
            safety: 'safe',
        },
    });

    // Tuner plugin reads merged tunings for its picker, contributes custom
    // tunings via the server-side TuningProviderRegistry, and emits
    // tunings-updated after any custom tuning is saved or deleted.
    capabilities.registerParticipant('plugin.tuner', {
        tuning: {
            roles: ['contributor', 'requester'],
            operations: ['get-tunings'],
            emits: ['tunings-updated'],
            mode: 'active',
            compatibility: 'none',
            safety: 'safe',
        },
    });

    window.slopsmith.tunings = Object.freeze({
        version: 1,
        get: function () {
            return fetch('/api/tunings').then(function (r) { return r.json(); });
        },
    });
})();
