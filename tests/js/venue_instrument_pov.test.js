'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const pov = require('../../static/v3/venue-instrument-pov.js');

test('resolveVenueInstrumentPov maps guitar arrangements', () => {
    assert.equal(pov.resolveVenueInstrumentPov('Lead'), 'guitar');
    assert.equal(pov.resolveVenueInstrumentPov('Rhythm'), 'guitar');
    assert.equal(pov.resolveVenueInstrumentPov('guitar'), 'guitar');
    assert.equal(pov.resolveVenueInstrumentPov('Combo'), 'guitar');
});

test('resolveVenueInstrumentPov maps bass drums and piano', () => {
    assert.equal(pov.resolveVenueInstrumentPov('Bass'), 'bass');
    assert.equal(pov.resolveVenueInstrumentPov('Drums'), 'drums');
    assert.equal(pov.resolveVenueInstrumentPov('drum'), 'drums');
    assert.equal(pov.resolveVenueInstrumentPov('Piano'), 'piano');
    assert.equal(pov.resolveVenueInstrumentPov('Keys'), 'piano');
    assert.equal(pov.resolveVenueInstrumentPov('keyboard'), 'piano');
});

test('resolveVenueInstrumentPov maps vocals and karaoke labels', () => {
    assert.equal(pov.resolveVenueInstrumentPov('Vocals'), 'vocals');
    assert.equal(pov.resolveVenueInstrumentPov('karaoke'), 'vocals');
    assert.equal(pov.resolveVenueInstrumentPov('vocal'), 'vocals');
    assert.equal(pov.resolveVenueInstrumentPov('lyrics'), 'vocals');
    assert.equal(pov.resolveVenueInstrumentPov('lyric'), 'vocals');
    assert.equal(pov.resolveVenueInstrumentPov('sing'), 'vocals');
    assert.equal(pov.resolveVenueInstrumentPov('singing'), 'vocals');
    assert.equal(pov.isVocalsKaraokeArrangement('Vocals'), true);
});

test('resolveVenueInstrumentPov defaults unknown to guitar', () => {
    assert.equal(pov.resolveVenueInstrumentPov(''), 'guitar');
    assert.equal(pov.resolveVenueInstrumentPov(null), 'guitar');
    assert.equal(pov.resolveVenueInstrumentPov('ShowLights'), 'guitar');
    assert.equal(pov.resolveVenueInstrumentPov('BasslineKeys'), 'guitar');
});

test('POV_IDS lists supported venue POVs including vocals', () => {
    assert.deepEqual(pov.POV_IDS, ['guitar', 'bass', 'drums', 'piano', 'vocals']);
});

test('integrate-venue-pov-plate.sh accepts vocals POV', () => {
    const script = fs.readFileSync(
        path.join(__dirname, '..', '..', 'scripts', 'integrate-venue-pov-plate.sh'),
        'utf8',
    );
    assert.match(script, /vocals/);
    assert.match(script, /guitar bass drums piano vocals/);
    assert.match(script, /\$\{POV\}-pov-bg\.png/);
});
