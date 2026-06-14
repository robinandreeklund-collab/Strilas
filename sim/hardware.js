// hardware.js — STRILAS hårdvarumodeller (porterade från fysiksimuleringen)
// All "riktig" hårdvara modelleras här: ballistik, IR-länkbudget, zoner,
// MilesTag II-paket, rekyl/IMU, vapenprofiler.

// ---------- linjär interpolation ----------
function interp(x, xs, ys) {
  if (x <= xs[0]) return ys[0];
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
  let lo = 0, hi = xs.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] < x) lo = m; else hi = m; }
  const t = (x - xs[lo]) / (xs[hi] - xs[lo]);
  return ys[lo] + t * (ys[hi] - ys[lo]);
}

// ---------- BALLISTIK (M4 / 5.56, kd kalibrerad: v(300m)≈600 m/s) ----------
const _g = 9.81, _v0 = 880, _kd = 0.001277, _dt = 1e-4;
const _X = [0], _Y = [0], _T = [0], _V = [_v0];
(function () {
  let x = 0, y = 0, vx = _v0, vy = 0, t = 0;
  while (x < 320) {
    const s = Math.hypot(vx, vy);
    vx += -_kd * s * vx * _dt; vy += (-_g - _kd * s * vy) * _dt;
    x += vx * _dt; y += vy * _dt; t += _dt;
    _X.push(x); _Y.push(-y); _T.push(t); _V.push(Math.hypot(vx, vy));
  }
})();
// flygtid/drop skalas grovt med vapnets mynningshastighet
export function tof(R, v0 = 880) { return interp(R, _X, _T) * (880 / v0); }
export function drop(R, v0 = 880) { return interp(R, _X, _Y) * Math.pow(880 / v0, 2); }
export function vAt(R) { return interp(R, _X, _V); }

// ---------- IR-LÄNKBUDGET (SFH 4715AS + TSOP4856) ----------
const omega = (deg) => 2 * Math.PI * (1 - Math.cos(deg * Math.PI / 180));
const I_AXIS_1A = 0.9, PHI_1A = I_AXIS_1A * omega(45);
export function emitterIe(If, halfDeg, nLed = 2, lensEff = 0.6) {
  const der = Math.max(1 - 0.03 * (If - 1), 0.7);
  const Phi = PHI_1A * If * der * nLed;
  return lensEff * Phi / omega(halfDeg);     // W/sr on-axis
}
export const EMIN_IDEAL = 0.35e-3;           // W/m^2 TSOP4856 tröskel (lab)
export const FILTER_GAIN = 4.0;              // 860 nm bandpass i sol
export const ENVIRONMENTS = {
  'Inomhus / mörker': 1,
  'Molnigt / skugga': 10,
  'Starkt solljus': 30,
  'Direkt sol mot sensor': 100,
};
export function maxRange(If, halfDeg, envMult, nLed = 2, filter = false) {
  const Emin = EMIN_IDEAL * envMult / (filter ? FILTER_GAIN : 1);
  return Math.sqrt(emitterIe(If, halfDeg, nLed) / Emin);
}
export const beamRadius = (R, halfDeg) => R * Math.tan(halfDeg * Math.PI / 180);

// ---------- KROPPSZONER (TSOP4856-detektorer) ----------
export const ZONES = [
  { name: 'Huvud', zl: 1.60, zh: 1.80, hw: 0.105, mult: 3.0, color: 0xff5c5c },
  { name: 'Bröst', zl: 1.25, zh: 1.60, hw: 0.24, mult: 1.0, color: 0xffb000 },
  { name: 'Mage', zl: 0.95, zh: 1.25, hw: 0.20, mult: 0.8, color: 0xffd35c },
  { name: 'Ben', zl: 0.00, zh: 0.95, hw: 0.165, mult: 0.5, color: 0x4aa3ff },
];
export const BODY_H = 1.80, BODY_HW = 0.25;
export function zoneAt(z, y) {
  for (const Z of ZONES) if (z >= Z.zl && z <= Z.zh && Math.abs(y) <= Z.hw) return Z;
  return null;
}

// ---------- MilesTag II-paket ----------
export function milestagShot(playerId, team, damage) {
  const p = (playerId & 0x7f).toString(2).padStart(7, '0');
  const t = (team & 0x3).toString(2).padStart(2, '0');
  const d = (damage & 0xf).toString(2).padStart(4, '0');
  const bits = '0' + p + t + d;                 // 14 bitar: typ(0)+ID+team+skada
  // airtime: header 2.4ms + 0.6 paus + 14*(burst+gap), burst snitt 0.9ms, gap 0.6ms
  const airtime = 2.4 + 0.6 + 14 * (0.9 + 0.6);
  return { bits, fields: { playerId, team, damage }, airtimeMs: airtime };
}

// ---------- VAPENPROFILER ----------
export const PROFILES = {
  'M4 / 5.56': { v0: 880, beamHalf: 1.0, rofRpm: 720, dmg: 0x6, recoilDeg: 1.3, mag: 30, auto: true },
  'MP5 / 9mm': { v0: 400, beamHalf: 2.0, rofRpm: 800, dmg: 0x4, recoilDeg: 0.8, mag: 30, auto: true },
  'AWM / prickskytt': { v0: 900, beamHalf: 0.4, rofRpm: 40, dmg: 0xf, recoilDeg: 3.0, mag: 5, auto: false },
};

// ---------- REKYL / IMU ----------
// per-skott klättring (deg) + en parametrisk pitch-rate-puls för IMU-visning
export function imuRate(tSec, ampDps = 92, f = 22, tau = 0.018) {
  return ampDps * Math.sin(2 * Math.PI * f * tSec) * Math.exp(-tSec / tau);
}

// ===================== NIVÅ 3: 3D-BALLISTIK & GEOMETRI =====================

// Integrera kulans bana i 3D (Euler, 0.5 ms) — gravitation + drag + vektorvind.
// Returnerar samplade tillstånd var ~5 ms: [{t,x,y,z,v}], samt slutmarkör.
export function integrate3D(mx, my, mz, dx, dy, dz, v0, wind = [0, 0, 0], maxRange = 320) {
  const g = 9.81, kd = 0.001277, dt = 0.0005;
  let x = mx, y = my, z = mz, vx = dx * v0, vy = dy * v0, vz = dz * v0, t = 0, n = 0;
  const S = [{ t: 0, x, y, z, v: v0 }];
  while (t < 2.0 && y > -1.0) {
    const rvx = vx - wind[0], rvy = vy - wind[1], rvz = vz - wind[2];
    const sp = Math.hypot(rvx, rvy, rvz);
    vx += -kd * sp * rvx * dt; vy += (-g - kd * sp * rvy) * dt; vz += -kd * sp * rvz * dt;
    x += vx * dt; y += vy * dt; z += vz * dt; t += dt; n++;
    if (n % 10 === 0) S.push({ t, x, y, z, v: Math.hypot(vx, vy, vz) });
    if (Math.hypot(x - mx, z - mz) > maxRange) break;
  }
  return S;
}

// Kroppskapslar (postur: stående) vid fotposition (tx,0,tz). Vertikala segment.
export function bodyCapsules(tx, tz) {
  return [
    { name: 'Huvud', p0: [tx, 1.62, tz], p1: [tx, 1.78, tz], r: 0.10, mult: 3.0, color: 0xff5c5c },
    { name: 'Bröst', p0: [tx, 1.25, tz], p1: [tx, 1.55, tz], r: 0.17, mult: 1.0, color: 0xffb000 },
    { name: 'Mage', p0: [tx, 0.95, tz], p1: [tx, 1.15, tz], r: 0.16, mult: 0.8, color: 0xffd35c },
    { name: 'Ben', p0: [tx, 0.10, tz], p1: [tx, 0.85, tz], r: 0.14, mult: 0.5, color: 0x4aa3ff },
  ];
}

// Kortaste avstånd mellan två segment (p1-q1) och (p2-q2). (Ericson, Real-Time CD)
export function closestSegSeg(p1, q1, p2, q2) {
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const d1 = sub(q1, p1), d2 = sub(q2, p2), r = sub(p1, p2);
  const a = dot(d1, d1), e = dot(d2, d2), f = dot(d2, r);
  let s, tt;
  const EPS = 1e-9;
  if (a <= EPS && e <= EPS) { s = 0; tt = 0; }
  else if (a <= EPS) { s = 0; tt = Math.min(Math.max(f / e, 0), 1); }
  else {
    const c = dot(d1, r);
    if (e <= EPS) { tt = 0; s = Math.min(Math.max(-c / a, 0), 1); }
    else {
      const b = dot(d1, d2), den = a * e - b * b;
      s = den > EPS ? Math.min(Math.max((b * f - c * e) / den, 0), 1) : 0;
      tt = (b * s + f) / e;
      if (tt < 0) { tt = 0; s = Math.min(Math.max(-c / a, 0), 1); }
      else if (tt > 1) { tt = 1; s = Math.min(Math.max((b - c) / a, 0), 1); }
    }
  }
  const c1 = [p1[0] + d1[0] * s, p1[1] + d1[1] * s, p1[2] + d1[2] * s];
  const c2 = [p2[0] + d2[0] * tt, p2[1] + d2[1] * tt, p2[2] + d2[2] * tt];
  return { dist: Math.hypot(c1[0] - c2[0], c1[1] - c2[1], c1[2] - c2[2]), point: c1 };
}
