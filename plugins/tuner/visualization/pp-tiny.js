(function () {
    'use strict';

    // ── Constants ─────────────────────────────────────────────────────
    var _TUNER_PT_IN_TUNE_THR  = 2;
    var _TUNER_PT_LED_COUNT    = 11;
    var _TUNER_PT_CENTS_RANGE  = 50;

    // Display colours
    var _TUNER_PT_LIT   = '#ff2200';
    var _TUNER_PT_UNLIT = '#1a0000';

    var _TUNER_PT_BG    = '#0d0000';

    // ── 8-segment map ─────────────────────────────────────────────────
    // Segments indexed: [a, b, c, d, e, f, g1, g2]
    var _TUNER_PT_SEGMENTS = {
        //         a      b      c      d      e      f      g1     g2
        'A': [ true,  true,  true,  false, true,  true,  true,  true  ],
        'B': [ false, false, true,  true,  true,  true,  true,  true  ],
        'C': [ true,  false, false, true,  true,  true,  false, false ],
        'D': [ false, true,  true,  true,  true,  false, true,  true  ],
        'E': [ true,  false, false, true,  true,  true,  true,  false ],
        'F': [ true,  false, false, false, true,  true,  true,  false ],
        'G': [ true,  false, true,  true,  true,  true,  false, true  ],
        ' ': [ false, false, false, false, false, false, false, false ],
    };

    // Instance counter for unique SVG gradient IDs
    var _ppTinyCount = 0;

    window['_tunerViz_pp-tiny'] = function (container) {
        'use strict';

        // ── SVG frame ─────────────────────────────────────────────────
        // Shape: semi-circle (r = W/2) + rectangle (h = W/4)
        // Total height = W/2 + W/4 = 3W/4  →  aspect-ratio 4:3
        // viewBox "0 0 100 75" (75 = 3/4 × 100).
        //   Semi-circle arc: centre (50,50), r=50, from (0,50) to (100,50)
        //   Rectangle:       y 50→75, full width, small rounded bottom corners
        // Face inset 4 units on all sides:
        //   Semi-circle arc: centre (50,50), r=46, from (4,50) to (96,50)
        //   Rectangle:       y 50→71  (75−4=71)
        var _gradId = 'ppTinyFrameGrad' + (++_ppTinyCount);

        var panel = document.createElement('div');
        panel.style.cssText = 'position:relative;width:100%;aspect-ratio:4/3;user-select:none;';

        // SVG draws the gray frame + dark face shape
        var frameSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        frameSvg.setAttribute('viewBox', '0 0 100 75');
        frameSvg.setAttribute('preserveAspectRatio', 'none');
        frameSvg.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;display:block;';

        var _brushId      = 'ppTinyBrush'      + _ppTinyCount;
        var _bevelBrushId = 'ppTinyBevelBrush' + _ppTinyCount;

        var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

        // Main face: metallic gradient with multiple highlight/shadow bands
        var grad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        grad.setAttribute('id', _gradId);
        grad.setAttribute('x1', '0.2'); grad.setAttribute('y1', '0');
        grad.setAttribute('x2', '0.8'); grad.setAttribute('y2', '1');
        [['0%','#f2f2f2'],['14%','#d0d0d0'],['30%','#888888'],['46%','#bababa'],['62%','#7e7e7e'],['80%','#c2c2c2'],['100%','#6a6a6a']].forEach(function(s) {
            var stop = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop.setAttribute('offset', s[0]); stop.setAttribute('stop-color', s[1]);
            grad.appendChild(stop);
        });
        defs.appendChild(grad);


        function _makeBrushFilter(id, freqX, freqY, seed, contrast, base) {
            var c = contrast || 0.4, b = base !== undefined ? base : 0.25;
            var v = c + ' 0 0 0 ' + b + '  ' + c + ' 0 0 0 ' + b + '  ' + c + ' 0 0 0 ' + b + '  0 0 0 1 0';
            var f = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
            f.setAttribute('id', id);
            f.setAttribute('color-interpolation-filters', 'sRGB');
            var t = document.createElementNS('http://www.w3.org/2000/svg', 'feTurbulence');
            t.setAttribute('type', 'fractalNoise'); t.setAttribute('baseFrequency', freqX + ' ' + freqY);
            t.setAttribute('numOctaves', '2'); t.setAttribute('seed', seed); t.setAttribute('result', 'noise');
            var cm = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
            cm.setAttribute('type', 'matrix'); cm.setAttribute('in', 'noise');
            cm.setAttribute('values', v);
            cm.setAttribute('result', 'grayNoise');
            var bl = document.createElementNS('http://www.w3.org/2000/svg', 'feBlend');
            bl.setAttribute('in', 'SourceGraphic'); bl.setAttribute('in2', 'grayNoise');
            bl.setAttribute('mode', 'soft-light'); bl.setAttribute('result', 'blended');
            var cp = document.createElementNS('http://www.w3.org/2000/svg', 'feComposite');
            cp.setAttribute('in', 'blended'); cp.setAttribute('in2', 'SourceGraphic'); cp.setAttribute('operator', 'in');
            f.appendChild(t); f.appendChild(cm); f.appendChild(bl); f.appendChild(cp);
            return f;
        }
        defs.appendChild(_makeBrushFilter(_brushId,      '0.65', '0.015', '3', 0.4,  0.25)); // horizontal grain — main arc face
        defs.appendChild(_makeBrushFilter(_bevelBrushId, '0.45', '0.015', '7', 0.65, 0.08)); // horizontal grain, lower freq, higher contrast — bevel face

        frameSvg.appendChild(defs);

        // Main frame — restored with original rounded corners, unchanged
        var framePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        framePath.setAttribute('d', 'M 0,50 A 50,50 0 0 1 100,50 L 100,73 Q 100,75 98,75 L 2,75 Q 0,75 0,73 Z');
        framePath.setAttribute('fill', 'url(#' + _gradId + ')');
        framePath.setAttribute('filter', 'url(#' + _brushId + ')');
        frameSvg.appendChild(framePath);

        // Bevel trapezoid — sits on top of the main frame, covers only the bottom strip.
        // Sides meet the corner curves at their t=0.5 midpoints (de Casteljau):
        //   Right midpoint: (99.5, 74.5); lower-half bezier: Q 99,75 98,75
        //   Left  midpoint: (0.5,  74.5); lower-half bezier: Q 1,75 0.5,74.5 (path direction reversed)
        // 45° sides: Δx=Δy=5.5 each ✓ — top edge y=69, x=6 to x=94
        var bevelPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        bevelPath.setAttribute('d', 'M 6,69 L 94,69 L 99.5,74.5 Q 99,75 98,75 L 2,75 Q 1,75 0.5,74.5 Z');
        bevelPath.setAttribute('fill', '#c0c0c0');
        bevelPath.setAttribute('filter', 'url(#' + _bevelBrushId + ')');
        frameSvg.appendChild(bevelPath);

        var faceBgPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        faceBgPath.setAttribute('d', 'M 4,50 A 46,46 0 0 1 96,50 L 96,70 Q 96,71 95,71 L 5,71 Q 4,71 4,70 Z');
        faceBgPath.setAttribute('fill', '#080808');
        frameSvg.appendChild(faceBgPath);

        panel.appendChild(frameSvg);

        // ── Black panel face (content host) ───────────────────────────
        // Face occupies inset 4 units in viewBox coords:
        //   left: 4/100 = 4%,  top: 4/75 = 5.333%
        //   width: 92/100 = 92%,  height: 67/75 = 89.333%
        var face = document.createElement('div');
        face.style.cssText = 'position:absolute;left:4%;top:5.333%;width:92%;height:89.333%;overflow:hidden;';
        panel.appendChild(face);

        // ── Arc geometry ──────────────────────────────────────────────
        // Face SVG inset: x 4–96, y 4–71  (width=92, height=67 in panel units).
        // Arc centre in panel SVG = (50, 50)  →  in face-div %:
        //   cx = (50−4)/92×100 = 50 %
        //   cy = (50−4)/67×100 = 68.657 %
        // Face aspect A = 92/67 ≈ 1.3731.
        // For a physical circle of radius r (% of face-width):
        //   x = cx + r·cos(θ)        (face-width %)
        //   y = cy − r·A·sin(θ)      (face-height %; A corrects non-square face)
        // Separator SVG arc (viewBox 0 0 100 100, preserveAspectRatio=none):
        //   rx = r (x-units ≡ face-width %), ry = r·A (y-units ≡ face-height %)
        // Radii (r in % of face_width, max=46):
        //   LEDs   r=40 → top at (50%, 14%)
        //   line   r=35 → top at (50%, 21%)
        //   labels r=30 → top at (50%, 27%)

        var _ARC_CX         = 50;
        var _ARC_CY         = 68.657;           // % of face height
        var _ARC_ASPECT     = 92 / 67;          // face width / face height
        var _ARC_R_LEDS     = 40;
        var _ARC_R_LINE     = 35;
        var _ARC_R_LABELS   = 30;
        var _ARC_CENTRE_IDX = Math.floor(_TUNER_PT_LED_COUNT / 2); // 5

        function _arcPoint(i, r) {
            var angleDeg = 180 - i * (180 / (_TUNER_PT_LED_COUNT - 1));
            var rad = angleDeg * Math.PI / 180;
            return {
                x: _ARC_CX + r * Math.cos(rad),
                y: _ARC_CY - r * _ARC_ASPECT * Math.sin(rad),
            };
        }

        // ── 1. LED arc ────────────────────────────────────────────────
        var leds = [];
        for (var i = 0; i < _TUNER_PT_LED_COUNT; i++) {
            var pt  = _arcPoint(i, _ARC_R_LEDS);

            var led = document.createElement('div');
            led.style.position     = 'absolute';
            led.style.left         = pt.x.toFixed(2) + '%';
            led.style.top          = pt.y.toFixed(2) + '%';
            led.style.transform    = 'translate(-50%, -50%)';
            led.style.width        = '5%';
            led.style.aspectRatio  = '1 / 1';
            led.style.borderRadius = '50%';

            var isCentre = (i === _ARC_CENTRE_IDX);
            led.style.background = isCentre
                ? 'radial-gradient(circle at 35% 35%, #3a0000, #1a0000)'
                : 'radial-gradient(circle at 35% 35%, #2a2000, #141000)';
            led.style.border    = '1px solid ' + (isCentre ? '#400' : '#420');
            led.style.boxShadow = 'none';

            face.appendChild(led);
            leds.push(led);
        }

        // ── 2. White separator arc (SVG) ──────────────────────────────
        // Semicircle from (cx−r, cy) to (cx+r, cy) through the top.
        // viewBox "0 0 100 100" fills the square face exactly; rx=ry gives a
        // true circle. sweep=1 (clockwise in SVG y-down space) draws upward.
        var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 100 100');
        svg.setAttribute('preserveAspectRatio', 'none');
        svg.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;overflow:visible';

        // SVG viewBox 0 0 100 100, preserveAspectRatio=none:
        // x-unit = 1% face-width, y-unit = 1% face-height.
        // For a physical circle: rx=r, ry=r×A (corrects non-square face).
        var x0Line = _ARC_CX - _ARC_R_LINE;
        var x1Line = _ARC_CX + _ARC_R_LINE;
        var ryLine = (_ARC_R_LINE * _ARC_ASPECT).toFixed(3);
        var arcPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        arcPath.setAttribute('d',
            'M ' + x0Line + ',' + _ARC_CY.toFixed(3) +
            ' A ' + _ARC_R_LINE + ',' + ryLine + ' 0 0 1 ' +
            x1Line + ',' + _ARC_CY.toFixed(3));
        arcPath.setAttribute('stroke', 'rgba(255,255,255,0.65)');
        arcPath.setAttribute('stroke-width', '0.8');
        arcPath.setAttribute('fill', 'none');
        svg.appendChild(arcPath);
        face.appendChild(svg);

        // ── 3. Range labels ───────────────────────────────────────────
        var labelDefs = [
            { text: '-50', i: 0 },
            { text:  '0',  i: _ARC_CENTRE_IDX },
            { text: '+50', i: _TUNER_PT_LED_COUNT - 1 },
        ];
        labelDefs.forEach(function (d) {
            var pt = _arcPoint(d.i, _ARC_R_LABELS);
            var el = document.createElement('div');
            el.style.position   = 'absolute';
            el.style.left       = pt.x.toFixed(2) + '%';
            el.style.top        = pt.y.toFixed(2) + '%';
            el.style.transform  = 'translate(-50%, -50%)';
            el.style.color      = '#cccccc';
            el.style.fontSize   = '50%';
            el.style.fontWeight = 'bold';
            el.style.fontFamily = 'sans-serif';
            el.style.lineHeight = '1';
            el.textContent      = d.text;
            face.appendChild(el);
        });

        // ── 4. LCD display (letter + # inside one box) ────────────────
        // top=50%, height=35% → bottom=85%, centre=67.5%.
        var displayWrap = document.createElement('div');
        displayWrap.style.cssText = [
            'position:absolute',
            'left:50%',
            'top:50%',
            'transform:translateX(-50%)',
            'width:23%',
            'height:35%',
            'background:' + _TUNER_PT_BG,
            'border-radius:3px',
            'border:1px solid #2a0000',
            'display:flex',
            'flex-direction:row',
            'align-items:center',
            'justify-content:center',
            'padding:4%',
            'box-sizing:border-box',
            'box-shadow:inset 0 0 8px #000'
        ].join(';');
        face.appendChild(displayWrap);

        // Letter digit (8-segment SVG, viewBox 100×200)
        // T=16, G=5, CH=6, mid-gap=3 — thicker segs, uniform 5-unit gaps
        // horiz: (xL+CH,y0),(xR-CH,y0),(xR,y0+T/2),(xR-CH,y1),(xL+CH,y1),(xL,y0+T/2)
        // vert:  (x+T/2,y0),(x+T,y0+CH),(x+T,y1-CH),(x+T/2,y1),(x,y1-CH),(x,y0+CH)
        var segSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        segSvg.setAttribute('viewBox', '0 0 100 200');
        segSvg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        segSvg.style.cssText = 'width:55%;aspect-ratio:1/2;flex-shrink:0;overflow:visible;';
        displayWrap.appendChild(segSvg);

        var segmentEls = {};

        function _makeSeg(key, points) {
            var el = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            el.setAttribute('points', points);
            el.setAttribute('fill', _TUNER_PT_UNLIT);
            segSvg.appendChild(el);
            segmentEls[key] = el;
        }

        _makeSeg('a',  '11,5    89,5    95,13   89,21   11,21   5,13');
        _makeSeg('b',  '87,26   95,32   95,81   87,87   79,81   79,32');
        _makeSeg('c',  '87,113  95,119  95,168  87,174  79,168  79,119');
        _makeSeg('d',  '11,179  89,179  95,187  89,195  11,195  5,187');
        _makeSeg('e',  '13,113  21,119  21,168  13,174  5,168   5,119');
        _makeSeg('f',  '13,26   21,32   21,81   13,87   5,81    5,32');
        _makeSeg('g1', '11,92   42.5,92 48.5,100 42.5,108 11,108 5,100');
        _makeSeg('g2', '57.5,92 89,92   95,100  89,108  57.5,108 51.5,100');

        // "#" symbol — absolute-positioned bottom-right, viewBox 90×90 (symbol fills it)
        // T=10, s=(90-20)/3=23.3 → bars and gaps evenly distributed
        var sharpSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        sharpSvg.setAttribute('viewBox', '0 0 90 90');
        sharpSvg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        sharpSvg.style.cssText = 'position:absolute;top:54%;right:6%;width:22%;aspect-ratio:1/1;overflow:visible;pointer-events:none;';
        displayWrap.appendChild(sharpSvg);

        var sharpParts = [];
        function _makeSharpPoly(points) {
            var el = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            el.setAttribute('points', points);
            el.setAttribute('fill', _TUNER_PT_UNLIT);
            sharpSvg.appendChild(el);
            sharpParts.push(el);
        }

        // left vert, right vert, top horiz, bottom horiz — all 90 units, T=10, CH=4, s=23.3
        _makeSharpPoly('28.3,0   33.3,4   33.3,86  28.3,90  23.3,86  23.3,4');
        _makeSharpPoly('61.7,0   66.7,4   66.7,86  61.7,90  56.7,86  56.7,4');
        _makeSharpPoly('4,23.3   86,23.3  90,28.3  86,33.3  4,33.3   0,28.3');
        _makeSharpPoly('4,56.7   86,56.7  90,61.7  86,66.7  4,66.7   0,61.7');

        // "♭" symbol — same position as sharpSvg, shown in place of it for flat notes
        var flatSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        flatSvg.setAttribute('viewBox', '0 0 90 90');
        flatSvg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        flatSvg.style.cssText = 'position:absolute;top:54%;right:6%;width:22%;aspect-ratio:1/1;overflow:visible;pointer-events:none;display:none;';
        displayWrap.appendChild(flatSvg);
        var flatText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        flatText.setAttribute('x', '45');
        flatText.setAttribute('y', '82');
        flatText.setAttribute('text-anchor', 'middle');
        flatText.setAttribute('font-size', '85');
        flatText.setAttribute('font-family', 'Georgia, serif');
        flatText.setAttribute('fill', _TUNER_PT_UNLIT);
        flatText.textContent = '♭';
        flatSvg.appendChild(flatText);

        // ── 5. AUTO LED (lit when mode is 'free' or 'auto') ──────────
        // Anchored to the display's right edge (≈69%) at the display's
        // vertical midpoint (54% + 20% = 74%).
        var autoWrap = document.createElement('div');
        autoWrap.style.cssText = 'position:absolute;left:85%;top:92%;transform:translateY(-50%);display:flex;flex-direction:column;align-items:center;gap:4%;pointer-events:none';

        var autoLed = document.createElement('div');
        autoLed.style.cssText = [
            'width:6%',
            'aspect-ratio:1/1',
            'border-radius:50%',
            'background:radial-gradient(circle at 35% 35%, #3a0000, #1a0000)',
            'box-shadow:none',
            'border:1px solid #400',
            'flex-shrink:0'
        ].join(';');

        var autoLabel = document.createElement('span');
        autoLabel.style.cssText = 'color:#cccccc;font-size:52%;font-weight:bold;letter-spacing:0.05em;font-family:sans-serif;';
        autoLabel.textContent = 'AUTO';

        autoWrap.appendChild(autoLed);
        autoWrap.appendChild(autoLabel);
        face.appendChild(autoWrap);

        // ── Brand label ───────────────────────────────────────────────
        var brandLabel = document.createElement('div');
        brandLabel.style.cssText = [
            'position:absolute',
            'bottom:4%',
            'left:50%',
            'transform:translateX(-50%)',
            'color:#cccccc',
            'font-size:60%',
            'font-weight:bold',
            'letter-spacing:0.1em',
            'font-family:sans-serif',
            'pointer-events:none'
        ].join(';');
        brandLabel.textContent = 'PP-Tiny';
        face.appendChild(brandLabel);

        container.appendChild(panel);

        // ── Helpers ───────────────────────────────────────────────────

        function _setLed(index, lit) {
            var led      = leds[index];
            var isCentre = (index === _ARC_CENTRE_IDX);
            if (lit) {
                if (isCentre) {
                    led.style.background = 'radial-gradient(circle at 35% 35%, #ff6644, #cc1100)';
                    led.style.boxShadow  = '0 0 5px 2px #ff3300, 0 0 10px 4px #aa1100';
                    led.style.border     = '1px solid #ff4400';
                } else {
                    led.style.background = 'radial-gradient(circle at 35% 35%, #ffee66, #cc9900)';
                    led.style.boxShadow  = '0 0 5px 2px #ffcc00, 0 0 10px 4px #aa8800';
                    led.style.border     = '1px solid #ffbb00';
                }
            } else {
                if (isCentre) {
                    led.style.background = 'radial-gradient(circle at 35% 35%, #3a0000, #1a0000)';
                    led.style.boxShadow  = 'none';
                    led.style.border     = '1px solid #400';
                } else {
                    led.style.background = 'radial-gradient(circle at 35% 35%, #2a2000, #141000)';
                    led.style.boxShadow  = 'none';
                    led.style.border     = '1px solid #420';
                }
            }
        }

        function _updateLeds(cents, hasSignal) {
            if (!hasSignal) {
                for (var i = 0; i < _TUNER_PT_LED_COUNT; i++) _setLed(i, false);
                return;
            }
            var c = Math.max(-_TUNER_PT_CENTS_RANGE, Math.min(_TUNER_PT_CENTS_RANGE, cents));
            var targetIdx = _ARC_CENTRE_IDX + Math.round(c / 10);
            targetIdx = Math.max(0, Math.min(_TUNER_PT_LED_COUNT - 1, targetIdx));

            for (var j = 0; j < _TUNER_PT_LED_COUNT; j++) {
                var lit;
                if (c >= 0) {
                    lit = (j >= _ARC_CENTRE_IDX && j <= targetIdx);
                } else {
                    lit = (j <= _ARC_CENTRE_IDX && j >= targetIdx);
                }
                _setLed(j, lit);
            }
        }

        var _segKeys = ['a', 'b', 'c', 'd', 'e', 'f', 'g1', 'g2'];

        function _setSegment(segEl, lit) {
            segEl.setAttribute('fill', lit ? _TUNER_PT_LIT : _TUNER_PT_UNLIT);
            segEl.style.filter = lit ? 'drop-shadow(0 0 2px #ff4400) drop-shadow(0 0 5px #cc1100)' : 'none';
        }

        function _renderNote(letter) {
            var map = _TUNER_PT_SEGMENTS[letter ? letter.toUpperCase() : ' '] || _TUNER_PT_SEGMENTS[' '];
            for (var k = 0; k < _segKeys.length; k++) {
                _setSegment(segmentEls[_segKeys[k]], map[k]);
            }
        }

        function _setSharp(lit) {
            var fill   = lit ? _TUNER_PT_LIT : _TUNER_PT_UNLIT;
            var filter = lit ? 'drop-shadow(0 0 2px #ff4400) drop-shadow(0 0 5px #cc1100)' : 'none';
            for (var si = 0; si < sharpParts.length; si++) {
                sharpParts[si].setAttribute('fill', fill);
                sharpParts[si].style.filter = filter;
            }
        }
        function _setFlat(lit) {
            flatSvg.style.display = lit ? '' : 'none';
            if (lit) {
                flatText.setAttribute('fill', _TUNER_PT_LIT);
                flatText.style.filter = 'drop-shadow(0 0 2px #ff4400) drop-shadow(0 0 5px #cc1100)';
            }
        }

        function _setAuto(mode) {
            var lit = (mode === 'free' || mode === 'auto');
            autoLed.style.background = lit
                ? 'radial-gradient(circle at 35% 35%, #ff6644, #cc1100)'
                : 'radial-gradient(circle at 35% 35%, #3a0000, #1a0000)';
            autoLed.style.boxShadow  = lit ? '0 0 5px 1px #ff3300, 0 0 10px 2px #aa1100' : 'none';
            autoLed.style.border     = lit ? '1px solid #ff2200' : '1px solid #400';
        }

        // ── Public API ────────────────────────────────────────────────
        function update(note, cents, freq, mode) {
            _setAuto(mode);
            if (note === null) {
                _updateLeds(0, false);
                _renderNote(' ');
                sharpSvg.style.display = '';
                _setSharp(false);
                _setFlat(false);
                return;
            }
            var letter = note[0];
            var acc    = note.length > 1 ? note[1] : '';
            _updateLeds(cents, true);
            _renderNote(letter);
            if (acc === '#') {
                sharpSvg.style.display = '';
                _setSharp(true);
                _setFlat(false);
            } else if (acc === 'b') {
                sharpSvg.style.display = 'none';
                _setFlat(true);
            } else {
                sharpSvg.style.display = '';
                _setSharp(false);
                _setFlat(false);
            }
        }

        function destroy() {
            panel.remove();
        }

        return { update: update, destroy: destroy };
    };

}());
