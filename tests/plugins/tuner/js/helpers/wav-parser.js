'use strict';

/**
 * Minimal PCM WAV parser for Node.js test environments.
 * Supports: mono/stereo, 16-bit and 24-bit signed PCM (audio format 1).
 * Mixes all channels down to mono and returns a normalized Float32Array in [-1, 1].
 */
function parseWav(nodeBuffer) {
    // Node.js Buffer.buffer is a pooled ArrayBuffer; slice to get an exact view.
    const ab = nodeBuffer.buffer.slice(
        nodeBuffer.byteOffset,
        nodeBuffer.byteOffset + nodeBuffer.byteLength
    );
    const view = new DataView(ab);
    const bytes = new Uint8Array(ab);

    function fourCC(offset) {
        return String.fromCharCode(bytes[offset], bytes[offset + 1], bytes[offset + 2], bytes[offset + 3]);
    }

    if (fourCC(0) !== 'RIFF' || fourCC(8) !== 'WAVE') {
        throw new Error('Not a valid WAV file');
    }

    let audioFormat = 0, numChannels = 0, sampleRate = 0, bitsPerSample = 0;
    let dataStart = -1, dataSize = 0;

    let offset = 12;
    while (offset + 8 <= ab.byteLength) {
        const id = fourCC(offset);
        const size = view.getUint32(offset + 4, true);
        if (id === 'fmt ') {
            audioFormat   = view.getUint16(offset + 8,  true);
            numChannels   = view.getUint16(offset + 10, true);
            sampleRate    = view.getUint32(offset + 12, true);
            bitsPerSample = view.getUint16(offset + 22, true);
        } else if (id === 'data') {
            dataStart = offset + 8;
            dataSize  = size;
            break;
        }
        offset += 8 + size + (size & 1); // chunks are word-aligned
    }

    if (dataStart === -1) throw new Error('No data chunk found in WAV file');
    if (audioFormat !== 1) throw new Error(`Only PCM WAV supported (audio format ${audioFormat})`);
    if (bitsPerSample !== 16 && bitsPerSample !== 24) {
        throw new Error(`Only 16-bit and 24-bit PCM supported (got ${bitsPerSample}-bit)`);
    }

    const bytesPerSample = bitsPerSample >> 3;
    const bytesPerFrame = numChannels * bytesPerSample;
    const nFrames = Math.floor(dataSize / bytesPerFrame);
    if (dataStart + nFrames * bytesPerFrame > ab.byteLength) {
        throw new Error('WAV data chunk extends beyond end of file');
    }
    const samples = new Float32Array(nFrames);

    for (let i = 0; i < nFrames; i++) {
        let sum = 0;
        for (let ch = 0; ch < numChannels; ch++) {
            const byteOffset = dataStart + i * bytesPerFrame + ch * bytesPerSample;
            if (bitsPerSample === 16) {
                sum += view.getInt16(byteOffset, true);
            } else {
                // 24-bit: read 3 bytes little-endian, sign-extend from bit 23.
                const lo = bytes[byteOffset];
                const mi = bytes[byteOffset + 1];
                const hi = bytes[byteOffset + 2];
                const raw = (lo | (mi << 8) | (hi << 16));
                sum += raw & 0x800000 ? raw - 0x1000000 : raw;
            }
        }
        const scale = bitsPerSample === 16 ? 32768.0 : 8388608.0;
        samples[i] = (sum / numChannels) / scale;
    }
    return { samples, sampleRate };
}

module.exports = { parseWav };
