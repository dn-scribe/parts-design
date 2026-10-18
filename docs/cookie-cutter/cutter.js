// Image -> cookie cutter mesh. Pure functions, no DOM: usable from the page and from node.
(function (root) {
  "use strict";

  // Two-pass 3-4 chamfer distance (in pixels) from every cell to the nearest cell where src is 1.
  function chamfer(src, w, h) {
    const INF = 1e9, d = new Float32Array(w * h);
    for (let i = 0; i < d.length; i++) d[i] = src[i] ? 0 : INF;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x; let v = d[i];
      if (x > 0) v = Math.min(v, d[i - 1] + 3);
      if (y > 0) {
        v = Math.min(v, d[i - w] + 3);
        if (x > 0) v = Math.min(v, d[i - w - 1] + 4);
        if (x < w - 1) v = Math.min(v, d[i - w + 1] + 4);
      }
      d[i] = v;
    }
    for (let y = h - 1; y >= 0; y--) for (let x = w - 1; x >= 0; x--) {
      const i = y * w + x; let v = d[i];
      if (x < w - 1) v = Math.min(v, d[i + 1] + 3);
      if (y < h - 1) {
        v = Math.min(v, d[i + w] + 3);
        if (x < w - 1) v = Math.min(v, d[i + w + 1] + 4);
        if (x > 0) v = Math.min(v, d[i + w - 1] + 4);
      }
      d[i] = v;
    }
    for (let i = 0; i < d.length; i++) d[i] /= 3;
    return d;
  }

  // gray: Uint8 w*h (0..255). Returns Uint8 mask (1 = shape) padded by `pad` cells on each side.
  function threshold(gray, w, h, level, invert, pad) {
    const W = w + 2 * pad, H = h + 2 * pad, m = new Uint8Array(W * H);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const dark = gray[y * w + x] < level;
      m[(y + pad) * W + x + pad] = (dark !== invert) ? 1 : 0;
    }
    return { mask: m, w: W, h: H };
  }

  // Height grid (mm): blade centred on the mask outline, flange on the outside of it.
  // cx, cy = cell size in mm; opts in mm: bladeT, bladeH, baseT, flange.
  function heightGrid(mask, w, h, cx, cy, o) {
    const cell = (cx + cy) / 2;
    const inside = chamfer(mask.map(v => 1 - v), w, h);  // distance to background, for shape cells
    const outside = chamfer(mask, w, h);                  // distance to shape, for background cells
    const ht = new Float32Array(w * h), half = o.bladeT / 2 / cell, fl = o.flange / cell;
    for (let i = 0; i < ht.length; i++) {
      const s = mask[i] ? inside[i] - 0.5 : -(outside[i] - 0.5);
      if (Math.abs(s) <= half) ht[i] = o.baseT + o.bladeH;
      else if (s < 0 && -s <= half + fl) ht[i] = o.baseT;
    }
    return ht;
  }

  // Heightfield -> flat triangle soup (Float32Array of 9 floats per triangle). Origin bottom-left, y up.
  function meshFromHeights(ht, w, h, cx, cy) {
    const out = [];
    const tri = (a, b, c) => out.push(...a, ...b, ...c);
    const quad = (a, b, c, d) => { tri(a, b, c); tri(a, c, d); };
    const H = (x, y) => (x < 0 || y < 0 || x >= w || y >= h) ? 0 : ht[y * w + x];
    for (let r = 0; r < h; r++) for (let c = 0; c < w; c++) {
      const z = ht[r * w + c]; if (z <= 0) continue;
      const x0 = c * cx, x1 = x0 + cx, y1 = (h - r) * cy, y0 = y1 - cy;  // row 0 is the top of the image
      quad([x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]);          // top
      quad([x0, y0, 0], [x0, y1, 0], [x1, y1, 0], [x1, y0, 0]);          // bottom
      let n = H(c, r - 1);  if (n < z) quad([x0, y1, n], [x1, y1, n], [x1, y1, z], [x0, y1, z]);  // +y
      n = H(c, r + 1);      if (n < z) quad([x1, y0, n], [x0, y0, n], [x0, y0, z], [x1, y0, z]);  // -y
      n = H(c - 1, r);      if (n < z) quad([x0, y0, n], [x0, y1, n], [x0, y1, z], [x0, y0, z]);  // -x
      n = H(c + 1, r);      if (n < z) quad([x1, y1, n], [x1, y0, n], [x1, y0, z], [x1, y1, z]);  // +x
    }
    return new Float32Array(out);
  }

  function binaryStl(tris, name) {
    const n = tris.length / 9, buf = new ArrayBuffer(84 + n * 50), dv = new DataView(buf);
    const hdr = (name || "cookie-cutter").slice(0, 79);
    for (let i = 0; i < hdr.length; i++) dv.setUint8(i, hdr.charCodeAt(i) & 127);
    dv.setUint32(80, n, true);
    for (let t = 0, o = 84; t < n; t++, o += 50) {
      const p = t * 9, ux = tris[p+3]-tris[p], uy = tris[p+4]-tris[p+1], uz = tris[p+5]-tris[p+2];
      const vx = tris[p+6]-tris[p], vy = tris[p+7]-tris[p+1], vz = tris[p+8]-tris[p+2];
      let nx = uy*vz-uz*vy, ny = uz*vx-ux*vz, nz = ux*vy-uy*vx;
      const l = Math.hypot(nx, ny, nz) || 1; nx /= l; ny /= l; nz /= l;
      [nx, ny, nz].forEach((v, k) => dv.setFloat32(o + k * 4, v, true));
      for (let k = 0; k < 9; k++) dv.setFloat32(o + 12 + k * 4, tris[p + k], true);
    }
    return buf;
  }

  // One call: gray image + params -> {mask, w, h, tris}.
  // p: widthMm, heightMm (shape size, X/Y), bladeT, bladeH, baseT, flange, level, invert
  function build(gray, iw, ih, p) {
    const flangeCells = 2 + Math.ceil((p.flange + p.bladeT) / (p.widthMm / iw));
    const t = threshold(gray, iw, ih, p.level, p.invert, flangeCells);
    const cx = p.widthMm / iw, cy = p.heightMm / ih;
    const ht = heightGrid(t.mask, t.w, t.h, cx, cy, p);
    return { mask: t.mask, w: t.w, h: t.h, tris: meshFromHeights(ht, t.w, t.h, cx, cy) };
  }

  const api = { chamfer, threshold, heightGrid, meshFromHeights, binaryStl, build };
  if (typeof module !== "undefined") module.exports = api; else root.CookieCutter = api;
})(typeof self !== "undefined" ? self : this);
