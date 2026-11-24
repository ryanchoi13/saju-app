/* 오늘의 부적 그리기 (2026-11-17 정오님 결정).
 * 서버(daily_talisman.py)가 준 명세 {kind, domain, dir, element, layout, keys, seed} 만으로 SVG 를 만든다.
 * 같은 명세면 같은 그림이다(자체 난수 mulberry32, 브라우저 난수·날짜를 쓰지 않는다).
 * 부적 안에는 설명 글귀·도장·테두리·날짜 글씨를 두지 않는다. 붉은 붓획 한 톤.
 * 부품 이름(PARTS 키)은 서버 daily_talisman.py 의 DOMAIN_PARTS / SHINSAL_PARTS 와 같아야 한다.
 * 색: 종이 노랑·붓 주홍은 부적 그림 안에서만 쓰는 색이다(브랜드 토큰 예외, 실물 부적 색을 따른다). */
(function (root) {
    'use strict';
    var PAPER = '#F6C511', INK = '#C4231A';
    var VB_W = 200, VB_H = 334;                       // 3:5

    // ---------- 난수 ----------
    function rngOf(seed) {
        var a = (seed >>> 0) || 1;
        var next = function () {
            a = (a + 0x6D2B79F5) >>> 0;
            var t = a;
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
        return {
            random: next,
            uniform: function (lo, hi) { return lo + (hi - lo) * next(); },
            choice: function (list) { return list[Math.floor(next() * list.length)]; },
            shuffle: function (list) {
                for (var i = list.length - 1; i > 0; i--) {
                    var j = Math.floor(next() * (i + 1)), tmp = list[i]; list[i] = list[j]; list[j] = tmp;
                }
                return list;
            }
        };
    }

    // ---------- 붓획 ----------
    function catmull(pts, n) {
        var P = [pts[0]].concat(pts, [pts[pts.length - 1]]), out = [];
        for (var i = 1; i < P.length - 2; i++) {
            var p0 = P[i - 1], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2];
            for (var k = 0; k < n; k++) {
                var t = k / n, t2 = t * t, t3 = t2 * t;
                out.push([0, 1].map(function (d) {
                    return 0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 +
                        (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3);
                }));
            }
        }
        out.push([pts[pts.length - 1][0], pts[pts.length - 1][1]]);
        return out;
    }
    function linspace(a, b, n) {
        var out = [];
        for (var i = 0; i < n; i++) { var t = i / (n - 1); out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); }
        return out;
    }
    function interp(t, xs, ys) {
        if (t <= xs[0]) return ys[0];
        for (var i = 1; i < xs.length; i++) {
            if (t <= xs[i]) { var f = (t - xs[i - 1]) / (xs[i] - xs[i - 1]); return ys[i - 1] + (ys[i] - ys[i - 1]) * f; }
        }
        return ys[ys.length - 1];
    }
    var PROFILES = [
        [.55, 1.0, .95, .7, .38, .12],   // 눌렀다 빠짐
        [.9, 1.0, .8, .55, .3, .1],      // 처음부터 굵게
        [.35, .8, 1.0, .75, .4, .1]      // 들어가며 굵어졌다 빠짐
    ];
    function f1(x) { return (Math.round(x * 10) / 10).toFixed(1); }

    function brush(pts, w, rng, smooth, press) {
        var c = (pts.length === 2 || smooth === false) ? (pts.length > 2 ? catmull(pts, 10) : linspace(pts[0], pts[1], 22)) : catmull(pts, 14);
        var n = c.length, prof = press || rng.choice(PROFILES);
        var px = prof.map(function (_, i) { return i / (prof.length - 1); });
        var wobF = rng.uniform(7, 15), wobP = rng.uniform(0, 6);
        var ww = [], L = [], R = [];
        for (var i = 0; i < n; i++) {
            var t = i / (n - 1);
            ww.push(w * interp(t, px, prof) * (1 + 0.10 * Math.sin(t * wobF + wobP)));
        }
        for (i = 0; i < n; i++) {
            var a = c[Math.max(i - 1, 0)], b = c[Math.min(i + 1, n - 1)], span = (i === 0 || i === n - 1) ? 1 : 2;
            var dx = (b[0] - a[0]) / span, dy = (b[1] - a[1]) / span, ln = Math.hypot(dx, dy) + 1e-9;
            var nx = -dy / ln, ny = dx / ln;
            L.push([c[i][0] + nx * ww[i] / 2, c[i][1] + ny * ww[i] / 2]);
            R.push([c[i][0] - nx * ww[i] / 2, c[i][1] - ny * ww[i] / 2]);
        }
        var poly = L.concat(R.reverse()), d = 'M' + poly.map(function (p) { return f1(p[0]) + ',' + f1(p[1]); }).join(' L') + 'Z';
        return '<path d="' + d + '"/><circle cx="' + f1(c[0][0]) + '" cy="' + f1(c[0][1]) + '" r="' + f1(ww[0] / 2 * 0.9) + '"/>';
    }

    // ---------- 획 부품 (단위상자 0..1, y 아래로) ----------
    function box(x0, y0, x1, y1) {
        return [[[[x0, y0], [x1, y0]], 0], [[[x1, y0 - .01], [x1 + .01, y1]], 0],
            [[[x0, y0], [x0 - .01, y1]], 0], [[[x0 - .02, y1], [x1 + .02, y1]], 0]];
    }
    var PARTS = {
        tian: box(.1, .1, .9, .9).concat([[[[.5, .08], [.47, .5], [.5, .92]], 1], [[[.08, .5], [.5, .46], [.92, .5]], 1]]),
        kou: box(.15, .2, .85, .8),
        ri: box(.2, .08, .8, .92).concat([[[[.2, .5], [.5, .46], [.8, .5]], 1]]),
        yue: [[[[.2, .08], [.8, .08], [.78, .7], [.6, .95]], 1], [[[.2, .08], [.2, .9]], 0],
            [[[.2, .38], [.8, .38]], 0], [[[.2, .64], [.78, .64]], 0]],
        chuan: [[[[.2, .05], [.16, .95]], 1], [[[.5, .02], [.5, .98]], 1], [[[.8, .05], [.84, .95]], 1]],
        spiral: [[[[.5, .5], [.62, .42], [.66, .6], [.48, .72], [.3, .58], [.34, .3], [.62, .18], [.84, .36], [.84, .72], [.58, .9], [.26, .86]], 1]],
        wave: [[[[.05, .55], [.25, .2], [.45, .8], [.65, .25], [.95, .6]], 1]],
        cross: [[[[.1, .5], [.9, .5]], 1], [[[.5, .05], [.5, .85], [.4, .95]], 1]],
        dots: [[[[.15, .45], [.2, .7]], 1], [[[.45, .2], [.5, .6]], 1], [[[.8, .4], [.85, .72]], 1], [[[.05, .85], [.95, .85]], 1]],
        ren: [[[[.55, .05], [.4, .5], [.15, .95]], 1], [[[.5, .45], [.7, .7], [.9, .95]], 1]],
        ren2: [[[[.5, .08], [.2, .5], [.12, .95]], 1], [[[.45, .4], [.7, .72], [.9, .95]], 1], [[[.3, .45], [.8, .45]], 1]],
        gui: box(.2, .05, .8, .45).concat([[[[.5, .05], [.48, .45]], 1], [[[.2, .25], [.5, .22], [.8, .25]], 1],
            [[[.3, .55], [.2, .95]], 1], [[[.7, .55], [.82, .95]], 1], [[[.45, .62], [.7, .8], [.4, .92]], 1]]),
        yu: [[[[.05, .1], [.95, .1]], 1], [[[.5, .02], [.5, .3]], 1]].concat(box(.12, .3, .88, .92),
            [[[[.35, .45], [.4, .6]], 1], [[[.6, .45], [.65, .6]], 1]]),
        an: [[[[.5, .02], [.5, .14]], 1], [[[.08, .22], [.5, .12], [.92, .22]], 1], [[[.08, .22], [.06, .4]], 1],
            [[[.92, .22], [.94, .4]], 1], [[[.3, .5], [.7, .5], [.4, .75], [.25, .95], [.7, .9]], 1]],
        gok: [[[[.1, .1], [.9, .1]], 1], [[[.2, .28], [.8, .28]], 1], [[[.1, .46], [.9, .46]], 1],
            [[[.5, .05], [.5, .92], [.35, .98]], 1], [[[.22, .62], [.1, .95]], 1], [[[.8, .62], [.92, .95]], 1]],
        mu: [[[[.1, .4], [.9, .4]], 1], [[[.5, .05], [.5, .95]], 1], [[[.5, .45], [.15, .88]], 1], [[[.5, .45], [.85, .88]], 1]],
        to: [[[[.25, .3], [.75, .3]], 1], [[[.5, .08], [.5, .8]], 1], [[[.08, .9], [.92, .9]], 1]],
        su: [[[[.5, .05], [.5, .9], [.38, .98]], 1], [[[.1, .35], [.38, .5], [.2, .8]], 1], [[[.9, .35], [.62, .5], [.8, .8]], 1]],
        hwa: [[[[.5, .05], [.2, .92]], 1], [[[.5, .35], [.88, .92]], 1], [[[.22, .25], [.12, .5]], 1], [[[.8, .25], [.9, .52]], 1]],
        geum: [[[[.5, .04], [.2, .36]], 1], [[[.5, .04], [.8, .36]], 1], [[[.22, .46], [.78, .46]], 1],
            [[[.22, .63], [.78, .63]], 1], [[[.5, .46], [.5, .92]], 1], [[[.12, .9], [.88, .9]], 1]],
        ja: [[[[.22, .18], [.75, .18], [.45, .4]], 1], [[[.5, .4], [.5, .92], [.35, .86]], 1], [[[.08, .6], [.92, .6]], 1]],
        hook3: [[[[.1, .8], [.1, .3], [.3, .1], [.35, .35]], 1], [[[.45, .8], [.45, .3], [.65, .1], [.7, .35]], 1],
            [[[.8, .8], [.8, .3], [.95, .12], [.98, .38]], 1]],
        ladder: [[[[.15, .05], [.15, .95]], 1], [[[.85, .05], [.85, .95]], 1], [[[.15, .25], [.85, .25]], 1],
            [[[.15, .5], [.85, .5]], 1], [[[.15, .75], [.85, .75]], 1]],
        bei: box(.2, .1, .8, .62).concat([[[[.2, .28], [.5, .25], [.8, .28]], 1], [[[.2, .45], [.5, .43], [.8, .45]], 1],
            [[[.32, .72], [.2, .95]], 1], [[[.68, .72], [.82, .95]], 1]]),
        mu_tail: [[[[.15, .1], [.5, .5], [.2, .9], [.85, .8]], 1]],
        knot: [[[[.1, .3], [.5, .1], [.9, .3], [.5, .55], [.1, .8], [.5, .95], [.9, .75]], 1]]
    };
    var OVERLAY = ['dots', 'cross', 'wave', 'mu_tail', 'knot', 'chuan', 'hook3', 'mu'];
    var SAT_BY_ELEMENT = { wood: 'mu', fire: 'hwa', earth: 'to', metal: 'geum', water: 'su' };
    var SAT_BY_DOMAIN = { money: 'tian', people: 'ren', work: 'ladder', health: 'an' };

    function place(strokes, x, y, w, h, rng, width, o) {
        o = o || {};
        var jitter = o.jitter == null ? 0.03 : o.jitter, rot = o.rot || 0, shear = o.shear || 0;
        var cx = x + w / 2, cy = y + h / 2, cr = Math.cos(rot), sr = Math.sin(rot), out = '';
        for (var s = 0; s < strokes.length; s++) {
            var pts = strokes[s][0], smooth = strokes[s][1], P = [];
            if (pts.length === 2) {
                var a = pts[0][0], b = pts[0][1], c = pts[1][0], d = pts[1][1], bow = rng.uniform(-.06, .06);
                pts = [[a, b], [(a + c) / 2 - (d - b) * bow, (b + d) / 2 + (c - a) * bow], [c, d]];
            }
            for (var i = 0; i < pts.length; i++) {
                var u = pts[i][0] + rng.uniform(-jitter, jitter), v = pts[i][1] + rng.uniform(-jitter, jitter);
                var px = x + u * w + shear * (v - .5) * w, py = y + v * h, dx = px - cx, dy = py - cy;
                P.push([cx + dx * cr - dy * sr, cy + dx * sr + dy * cr]);
            }
            out += brush(P, width, rng, !!smooth);
        }
        return out;
    }

    // ---------- 명세 ----------
    var FALLBACK = { kind: 'shinsal', domain: 'work', dir: 'neutral', element: 'earth', layout: 'simple', keys: ['to', 'mu', 'ri'], seed: 1 };
    function clean(spec) {
        var s = spec && typeof spec === 'object' ? spec : FALLBACK, keys = (s.keys || []).filter(function (k) { return PARTS[k]; });
        if (keys.length < 2) keys = FALLBACK.keys.slice();
        var dir = ['good', 'neutral', 'caution'].indexOf(s.dir) >= 0 ? s.dir : 'neutral';
        return {
            domain: SAT_BY_DOMAIN[s.domain] ? s.domain : 'work', dir: dir,
            element: SAT_BY_ELEMENT[s.element] ? s.element : 'earth',
            layout: s.layout === 'dense' ? 'dense' : 'simple',
            keys: keys.slice(0, 4), seed: Number.isFinite(+s.seed) ? +s.seed : 1
        };
    }

    // ---------- 합성 ----------
    function paint(spec) {
        var S = clean(spec), rng = rngOf(S.seed), ink = [], dense = S.layout === 'dense', dr = S.dir;
        var sw = dense ? 8.4 : 9.2, H = VB_H, E = H - 300;
        ink.push(place(PARTS.hook3, 54, 3, 92, 26, rng, sw * .9));
        ink.push(brush([[10, 34], [60, 31], [140, 31], [190, 36]], sw * 1.3, rng, true, [.4, 1, 1, .8, .1]));
        var hv = dense ? rng.choice(['a', 'b', 'c', 'd']) : 's';
        if (hv === 'a') {
            ink.push(place(PARTS.yu, 14, 38, 82, 44, rng, sw * .95)); ink.push(place(PARTS.gui, 104, 38, 82, 46, rng, sw * .95));
        } else if (hv === 'b') {
            ink.push(place(PARTS.gui, 12, 38, 78, 46, rng, sw * .95)); ink.push(place(PARTS.yu, 102, 38, 86, 44, rng, sw * .95));
        } else if (hv === 'c') {
            ink.push(place(PARTS.yu, 60, 38, 86, 44, rng, sw));
            ink.push(place(PARTS.chuan, 16, 40, 36, 40, rng, sw * .85)); ink.push(place(PARTS.wave, 150, 42, 38, 30, rng, sw * .85));
        } else if (hv === 'd') {
            ink.push(place(PARTS.gui, 14, 38, 74, 46, rng, sw * .95, { shear: .15 }));
            ink.push(place(PARTS.ja, 96, 38, 40, 44, rng, sw * .9)); ink.push(place(PARTS.yu, 140, 40, 50, 42, rng, sw * .9));
        } else {
            ink.push(place(PARTS.yu, 46, 40, 108, 42, rng, sw * 1.05));
        }

        // 가운데 합자: 파자 부품을 겹쳐 쌓아 한 덩어리 글자처럼
        var keys = S.keys.slice(), top = 88, n = keys.length, each = (120 + E + 5 * (n - 1)) / n, y = top, i, k;
        for (i = 0; i < keys.length; i++) {
            if (dense) {
                var wdt = rng.uniform(80, 98), x = 100 - wdt / 2 + rng.uniform(-6, 6);
                ink.push(place(PARTS[keys[i]], x, y, wdt, each, rng, sw, { jitter: .04, rot: rng.uniform(-.12, .12), shear: rng.uniform(-.25, .25) }));
                if (rng.random() < .7) {
                    var k2 = rng.choice(OVERLAY);
                    ink.push(place(PARTS[k2], x + wdt * rng.uniform(.05, .3), y + each * rng.uniform(.1, .35), wdt * rng.uniform(.5, .75), each * rng.uniform(.5, .75), rng, sw * .85, { jitter: .05, rot: rng.uniform(-.3, .3) }));
                }
                y += each - 5;
            } else {
                var w2 = rng.uniform(60, 78);
                ink.push(place(PARTS[keys[i]], 100 - w2 / 2, y, w2, each, rng, sw, { rot: rng.uniform(-.06, .06) }));
                y += each - 2;
            }
        }
        var midBottom = y + 4, bot = midBottom + 6;

        // 닫힌 성곽(주의) / 길게 빠지는 양옆 획(좋음) / 보통은 틀 없음
        if (dr === 'caution') {
            var t = top - 6;
            ink.push(brush([[14, t], [100, t - 3], [186, t + 1]], sw * 1.25, rng, true, [1, 1, .9, .5, .12]));
            ink.push(brush([[186 + rng.uniform(-4, 3), t + 1], [188 + rng.uniform(-4, 3), (t + bot) / 2], [186 + rng.uniform(-6, 3), bot - rng.uniform(0, 16)]], sw * 1.25, rng, true, [1, 1, .8, .45, .12]));
            ink.push(brush([[14, t], [12, (t + bot) / 2], [14, bot]], sw * 1.25, rng, true, [1, 1, .8, .45, .12]));
            ink.push(brush([[12, bot + 1], [100, bot + 3], [188, bot]], sw * 1.25, rng, true, [.9, 1, .9, .5, .12]));
        } else if (dr === 'good') {
            ink.push(brush([[26 + rng.uniform(-5, 8), top - 4], [18 + rng.uniform(-4, 6), top + 50], [16 + rng.uniform(-3, 6), bot + rng.uniform(-14, 6)]], sw * 1.2, rng, true, [1, 1, .8, .4, .08]));
            ink.push(brush([[174 + rng.uniform(-8, 5), top - 4 + rng.uniform(0, 10)], [182 + rng.uniform(-6, 4), top + 50], [184 + rng.uniform(-6, 3), bot + rng.uniform(-24, 6)]], sw * 1.2, rng, true, [1, 1, .8, .4, .08]));
        }

        // 끝: 가로 큰 획 + 긴 세로 + 좌우로 빠지는 다리 (종이 안에 들어오게 길이를 맞춘다)
        var base = bot + 10; k = Math.min(1.6, (H - 20 - base) / 72);
        ink.push(brush([[30, base], [100, base - 3], [170, base + k]], sw * 1.5, rng, true, [.5, 1, 1, .7, .12]));
        ink.push(brush([[100, base - 4], [99, base + k * 36], [101, base + k * 76], [92, base + k * 88]], sw * 1.5, rng, true, [1, 1, .9, .6, .12]));
        ink.push(brush([[96, base + k * 4], [68, base + k * 22], [42, base + k * 46], [24, base + k * 68]], sw * 1.7, rng, true, [1, .95, .7, .35, .06]));
        ink.push(brush([[104, base + k * 4], [134, base + k * 20], [160, base + k * 44], [178, base + k * 66]], sw * 1.7, rng, true, [1, .95, .7, .35, .06]));
        ink.push(brush([[62, base + k * 12], [50, base + k * 30]], sw * .8, rng));
        ink.push(brush([[138, base + k * 12], [150, base + k * 30]], sw * .8, rng));
        ink.push(place(PARTS.tian, 78, base + k * 10, 44, 30, rng, sw * .8));

        // 위성 글자: 가운데 합자 좌우의 빈 자리에만
        var span = midBottom - top, ys = [top + 10, top + 10 + (span - 80) / 2, top + span - 75];
        var zs = rng.shuffle([[30, ys[0]], [30, ys[1]], [30, ys[2]], [152, ys[0]], [152, ys[1]], [152, ys[2]]]);
        var nsat = dense ? 5 : 3;
        for (i = 0; i < nsat; i++) {
            var key = i % 2 === 0 ? SAT_BY_ELEMENT[S.element] : rng.choice([SAT_BY_DOMAIN[S.domain], 'tian', 'ja']);
            ink.push(place(PARTS[key], zs[i][0], zs[i][1], 21, 21, rng, sw * .7, { jitter: .03 }));
        }
        var fy = midBottom - 38;
        ink.push(brush([[38, fy], [39, fy + 12], [38, fy + 26]], 3.4, rng, true, [1, .8, .3, .1]));
        ink.push(brush([[162, fy], [161, fy + 12], [162, fy + 26]], 3.4, rng, true, [1, .8, .3, .1]));
        return ink.join('');
    }

    // 화면에 넣는 SVG 문자열. 폭만 주면 3:5 로 높이를 맞춘다. 읽을 수 있는 글자는 어디에도 넣지 않는다.
    function compose(spec, opts) {
        opts = opts || {};
        var width = opts.width || 168, height = Math.round(width * VB_H / VB_W), id = opts.id ? ' id="' + opts.id + '"' : '';
        return '<svg' + id + ' xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + VB_W + ' ' + VB_H + '" width="' + width + '" height="' + height +
            '" role="img" aria-label="오늘의 부적"><rect width="' + VB_W + '" height="' + VB_H + '" fill="' + PAPER + '"/><g fill="' + INK + '">' + paint(spec) + '</g></svg>';
    }

    var api = { compose: compose, PARTS: PARTS, PAPER: PAPER, INK: INK, VIEWBOX: [VB_W, VB_H], clean: clean };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    root.DalhaTalisman = api;
})(typeof window !== 'undefined' ? window : globalThis);
