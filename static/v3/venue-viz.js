/*
 * fee[dB]ack v0.3.0 — Venue visualization adapter.
 *
 * "Venue" is a built-in viz picker entry that reuses the highway_3d renderer
 * while keeping vizSelection='venue' so venue mood FX stay enabled.
 */
(function (root) {
    'use strict';

    const VENUE_VIZ_ID = 'venue';
    const RENDERER_VIZ_ID = 'highway_3d';
    const PLAYER_CLASS = 'is-venue-visualization';

    let _selectedVizId = null;
    let _activeRendererId = null;

    function isVenueVisualization(vizMode) {
        return String(vizMode || '') === VENUE_VIZ_ID;
    }

    function resolveRendererVizId(vizMode) {
        return isVenueVisualization(vizMode) ? RENDERER_VIZ_ID : vizMode;
    }

    function readStoredVizSelection() {
        try {
            return localStorage.getItem('vizSelection') || 'default';
        } catch (_) {
            return 'default';
        }
    }

    function readVizSelection() {
        try {
            const sel = typeof document !== 'undefined' ? document.getElementById('viz-picker') : null;
            if (sel && sel.value) return String(sel.value);
            return readStoredVizSelection();
        } catch (_) {
            return 'default';
        }
    }

    function getSelectedVizId() {
        if (_selectedVizId) return _selectedVizId;
        return readVizSelection();
    }

    function syncVenuePlaceholder(vizMode) {
        try {
            const isVenue = isVenueVisualization(vizMode);
            const showDom = isVenue && !!(root && root.v3VenueScene3d &&
                typeof root.v3VenueScene3d.shouldShowDomPlaceholder === 'function' &&
                root.v3VenueScene3d.shouldShowDomPlaceholder());
            const badge = typeof document !== 'undefined' ? document.getElementById('v3-venue-mode-badge') : null;
            const wash = typeof document !== 'undefined' ? document.getElementById('v3-venue-scene-wash') : null;
            if (badge && badge.classList) {
                if (showDom) badge.classList.remove('hidden');
                else badge.classList.add('hidden');
            }
            if (wash && wash.classList) {
                if (showDom) wash.classList.remove('hidden');
                else wash.classList.add('hidden');
            }
        } catch (_) { /* visual-only */ }
    }

    function syncPlayerVizClass(vizMode) {
        try {
            const player = typeof document !== 'undefined' ? document.getElementById('player') : null;
            if (!player || !player.classList) return;
            player.classList.toggle(PLAYER_CLASS, isVenueVisualization(vizMode));
            syncVenuePlaceholder(vizMode);
        } catch (_) { /* visual-only */ }
    }

    function setSelectedVizId(id) {
        _selectedVizId = id == null ? null : String(id);
        syncPlayerVizClass(_selectedVizId);
    }

    function notifyRendererInstalled(rendererId) {
        _activeRendererId = rendererId == null ? null : String(rendererId);
    }

    function getState() {
        const player = typeof document !== 'undefined' ? document.getElementById('player') : null;
        const pickerViz = readVizSelection();
        const selectedViz = getSelectedVizId();
        const storedVizSelection = readStoredVizSelection();
        const moodApi = root && root.v3VenueMoodFx;
        return {
            selectedViz,
            storedVizSelection,
            pickerViz,
            activeRendererId: _activeRendererId,
            isVenueVisualization: isVenueVisualization(selectedViz),
            playerHasVenueClass: !!(player && player.classList && player.classList.contains(PLAYER_CLASS)),
            playerClasses: player ? String(player.className || '') : '',
            hasVenueMoodApi: !!(moodApi && typeof moodApi.getState === 'function'),
            venueMoodState: moodApi && typeof moodApi.getState === 'function' ? moodApi.getState() : null,
        };
    }

    const api = {
        VENUE_VIZ_ID,
        RENDERER_VIZ_ID,
        PLAYER_CLASS,
        isVenueVisualization,
        resolveRendererVizId,
        readVizSelection,
        readStoredVizSelection,
        getSelectedVizId,
        syncPlayerVizClass,
        setSelectedVizId,
        notifyRendererInstalled,
        getState,
    };

    if (root) root.v3VenueViz = api;
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
}(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : null)));
