// Auto-generated offline file://-safe UMD/IIFE bundle for HVACPhysicsLib.
(function(root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.HVACPhysics = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  "use strict";
  const _M = {};
  _M.Constants = (function() {
const kPi = 3.14159265358979323846;
const kTwoPi = 2.0 * kPi;
const kSqrt2 = 1.41421356237309504880;
const kSqrt3 = 1.73205080756887729353;

const kAtmPa = 101325.0;
const kAtmPsia = 14.6959487752;
const kKelvinOffset = 273.15;
const kRankineOffset = 459.67;

const kGravitySI = 9.80665;
const kGravityIP = 32.174048556;
const kUniversalGasSI = 8314.462618;
const kUniversalGasIP = 1545.349;
const kStefanBoltzmannSI = 5.670374419e-8;
const kStefanBoltzmannIP = 1.714e-9;

const kDryAirGasConstSI = 287.055;
const kDryAirGasConstIP = 53.352;
const kWaterMolRatio = 0.621945;
const kStdAirDensityIP = 0.075;
const kStdAirCpIP = 0.240;
const kGrainsPerLb = 7000.0;

const kBtuPerHrPerTon = 12000.0;
const kWattsPerTon = 3516.852842;
const kBtuPerHrPerKw = 3412.141633;
const kWattsPerHp = 745.69987158;
const kJPerKgPerBtuPerLb = 2326.0;
const kJPerKgKPerBtuPerLbR = 4186.8;
const kPaPerPsi = 6894.757293168;
const kPaPerInWC = 249.08891;
const kPaPerInHg = 3386.3886667;
const kPaPerMicron = 0.1333223684;
const kKgM3PerLbFt3 = 16.018463374;
const kM3sPerCfm = 0.0004719474432;
const kM3sPerGpm = 6.30901964e-5;
const kMsPerFpm = 0.00508;
const kKgSPerLbHr = 0.0001259978806;
const kMPerFt = 0.3048;
const kMPerIn = 0.0254;
const kNmPerFtLb = 1.3558179483;
const kWmKPerBtuHrFtF = 1.730734666;
const kWPerM2KPerBtuHrFt2F = 5.678263341;

const kGridFreqHz = 60.0;
const kOmega60 = kTwoPi * kGridFreqHz;

  return { kPi, kTwoPi, kSqrt2, kSqrt3, kAtmPa, kAtmPsia, kKelvinOffset, kRankineOffset, kGravitySI, kGravityIP, kUniversalGasSI, kUniversalGasIP, kStefanBoltzmannSI, kStefanBoltzmannIP, kDryAirGasConstSI, kDryAirGasConstIP, kWaterMolRatio, kStdAirDensityIP, kStdAirCpIP, kGrainsPerLb, kBtuPerHrPerTon, kWattsPerTon, kBtuPerHrPerKw, kWattsPerHp, kJPerKgPerBtuPerLb, kJPerKgKPerBtuPerLbR, kPaPerPsi, kPaPerInWC, kPaPerInHg, kPaPerMicron, kKgM3PerLbFt3, kM3sPerCfm, kM3sPerGpm, kMsPerFpm, kKgSPerLbHr, kMPerFt, kMPerIn, kNmPerFtLb, kWmKPerBtuHrFtF, kWPerM2KPerBtuHrFt2F, kGridFreqHz, kOmega60 };
  })();

  _M.Types = (function() {
const EStatusCode = Object.freeze({
  Ok: 0,
  Clamped: 1,
  OutOfRange: 2,
  InvalidInput: 3,
  DidNotConverge: 4,
  SingularCircuit: 5,
  FloatingIsland: 6,
  TopologyError: 7,
  Transcritical: 8,
  DryIceHazard: 9,
  SubcooledLiquid: 10,
  TwoPhase: 11,
  SuperheatedVapor: 12,
});

const EPhysicsWarn = Object.freeze({
  WarnNone: 0,
  WarnClamped: 1 << 0,
  WarnNearCritical: 1 << 1,
  WarnExtrapolated: 1 << 2,
  WarnTransportEstimated: 1 << 3,
  WarnFloatingIsland: 1 << 4,
  WarnGminFallback: 1 << 5,
  WarnFogCondensation: 1 << 6,
  WarnDryIceRisk: 1 << 7,
  WarnLowOilVelocity: 1 << 8,
  WarnFlashGasRisk: 1 << 9,
  WarnCavitationRisk: 1 << 10,
  WarnResonanceRisk: 1 << 11,
  WarnCondensateRisk: 1 << 12,
  WarnA2LChargeExceeded: 1 << 13,
  WarnIllConditioned: 1 << 14,
  // Reserved Frontier Thermal ROM bits: 15..22
  // Reserved Frontier Electrical ROM bits: 23..30
  WarnUnverifiedLimit: (1 << 31) >>> 0,
});

class Complex {
  constructor(re = 0.0, im = 0.0) {
    this.re = re;
    this.im = im;
  }
  add(o) { return new Complex(this.re + o.re, this.im + o.im); }
  sub(o) { return new Complex(this.re - o.re, this.im - o.im); }
  neg() { return new Complex(-this.re, -this.im); }
  mul(o) { return new Complex(this.re * o.re - this.im * o.im, this.re * o.im + this.im * o.re); }
  scale(s) { return new Complex(this.re * s, this.im * s); }
  conj() { return new Complex(this.re, -this.im); }
  abs() { return Math.hypot(this.re, this.im); }
  argRad() { return (Math.abs(this.re) < 1e-30 && Math.abs(this.im) < 1e-30) ? 0.0 : Math.atan2(this.im, this.re); }
  argDeg() { return this.argRad() * (180.0 / 3.14159265358979323846); }
  div(d) {
    if (!Number.isFinite(d.re) || !Number.isFinite(d.im)) return new Complex(0.0, 0.0);
    const ar = Math.abs(d.re);
    const ai = Math.abs(d.im);
    if (ar === 0.0 && ai === 0.0) return new Complex(0.0, 0.0);
    if (ar >= ai) {
      const r = d.im / d.re;
      const den = d.re + d.im * r;
      return new Complex((this.re + this.im * r) / den, (this.im - this.re * r) / den);
    }
    const r = d.re / d.im;
    const den = d.re * r + d.im;
    return new Complex((this.re * r + this.im) / den, (this.im * r - this.re) / den);
  }
}

function polarComplex(mag, angleDeg) {
  const rad = angleDeg * (3.14159265358979323846 / 180.0);
  return new Complex(mag * Math.cos(rad), mag * Math.sin(rad));
}

function clampFinite(v, lo, hi, warnBox = null) {
  if (lo > hi) { const t = lo; lo = hi; hi = t; }
  if (Number.isNaN(v)) {
    if (warnBox) warnBox.flags |= EPhysicsWarn.WarnClamped;
    return lo;
  }
  if (!Number.isFinite(v)) {
    if (warnBox) warnBox.flags |= EPhysicsWarn.WarnClamped;
    return v > 0.0 ? hi : lo;
  }
  if (v < lo) {
    if (warnBox) warnBox.flags |= EPhysicsWarn.WarnClamped;
    return lo;
  }
  if (v > hi) {
    if (warnBox) warnBox.flags |= EPhysicsWarn.WarnClamped;
    return hi;
  }
  return v;
}

function safeDiv(num, den, fallback = 0.0) {
  return (Number.isFinite(num) && Number.isFinite(den) && Math.abs(den) > 1e-15) ? (num / den) : fallback;
}

function lerpVal(a, b, t) {
  return a + (b - a) * t;
}

  return { polarComplex, clampFinite, safeDiv, lerpVal, Complex, EStatusCode, EPhysicsWarn };
  })();

  _M.Units = (function() {
const C = _M.Constants;
const { clampFinite } = _M.Types;

const fToC = (f) => (f - 32.0) * (5.0 / 9.0);
const cToF = (c) => c * (9.0 / 5.0) + 32.0;
const fToK = (f) => (f - 32.0) * (5.0 / 9.0) + C.kKelvinOffset;
const kToF = (k) => (k - C.kKelvinOffset) * (9.0 / 5.0) + 32.0;
const fToR = (f) => f + C.kRankineOffset;
const rToF = (r) => r - C.kRankineOffset;
const deltaFToDeltaK = (dF) => dF * (5.0 / 9.0);
const deltaKToDeltaF = (dK) => dK * (9.0 / 5.0);

const psiaToPa = (psia) => psia * C.kPaPerPsi;
const paToPsia = (pa) => pa / C.kPaPerPsi;
const psigToPsia = (psig, baroPsia = C.kAtmPsia) => psig + baroPsia;
const psiaToPsig = (psia, baroPsia = C.kAtmPsia) => psia - baroPsia;
const inHgVacToPsia = (inHgVac, baroPsia = C.kAtmPsia) => baroPsia - inHgVac * (C.kPaPerInHg / C.kPaPerPsi);
const psiaToInHgVac = (psia, baroPsia = C.kAtmPsia) => (baroPsia - psia) * (C.kPaPerPsi / C.kPaPerInHg);
const micronsToPa = (m) => m * C.kPaPerMicron;
const paToMicrons = (pa) => pa / C.kPaPerMicron;
const micronsToPsia = (m) => micronsToPa(m) / C.kPaPerPsi;
const psiaToMicrons = (psia) => paToMicrons(psia * C.kPaPerPsi);
const inWCToPa = (inWC) => inWC * C.kPaPerInWC;
const paToInWC = (pa) => pa / C.kPaPerInWC;
const inWCToPsi = (inWC) => inWCToPa(inWC) / C.kPaPerPsi;
const psiToInWC = (psi) => (psi * C.kPaPerPsi) / C.kPaPerInWC;
const ftWaterToPsi = (ft) => ft * 0.4335275;
const psiToFtWater = (psi) => psi / 0.4335275;
const barToPsia = (bar) => (bar * 100000.0) / C.kPaPerPsi;
const psiaToBar = (psia) => (psia * C.kPaPerPsi) / 100000.0;
const kPaToPsia = (kpa) => (kpa * 1000.0) / C.kPaPerPsi;
const psiaToKPa = (psia) => (psia * C.kPaPerPsi) / 1000.0;

const btuLbToJKg = (v) => v * C.kJPerKgPerBtuPerLb;
const jKgToBtuLb = (v) => v / C.kJPerKgPerBtuPerLb;
const btuLbRToJKgK = (v) => v * C.kJPerKgKPerBtuPerLbR;
const jKgKToBtuLbR = (v) => v / C.kJPerKgKPerBtuPerLbR;
const lbFt3ToKgM3 = (v) => v * C.kKgM3PerLbFt3;
const kgM3ToLbFt3 = (v) => v / C.kKgM3PerLbFt3;
const paSToCp = (v) => v * 1000.0;
const cpToPaS = (v) => v * 0.001;
const wmKToBtuHrFtF = (v) => v / C.kWmKPerBtuHrFtF;
const btuHrFtFToWmK = (v) => v * C.kWmKPerBtuHrFtF;
const uValueIPToSI = (v) => v * C.kWPerM2KPerBtuHrFt2F;
const uValueSIToIP = (v) => v / C.kWPerM2KPerBtuHrFt2F;

const btuHrToWatts = (v) => (v / C.kBtuPerHrPerKw) * 1000.0;
const wattsToBtuHr = (v) => v * 0.001 * C.kBtuPerHrPerKw;
const tonsToBtuHr = (v) => v * C.kBtuPerHrPerTon;
const btuHrToTons = (v) => v / C.kBtuPerHrPerTon;
const tonsToKw = (v) => v * C.kWattsPerTon * 0.001;
const hpToWatts = (v) => v * C.kWattsPerHp;
const wattsToHp = (v) => v / C.kWattsPerHp;
const cfmToM3s = (v) => v * C.kM3sPerCfm;
const m3sToCfm = (v) => v / C.kM3sPerCfm;
const fpmToMs = (v) => v * C.kMsPerFpm;
const msToFpm = (v) => v / C.kMsPerFpm;
const gpmToM3s = (v) => v * C.kM3sPerGpm;
const m3sToGpm = (v) => v / C.kM3sPerGpm;
const lbHrToKgS = (v) => v * C.kKgSPerLbHr;
const kgSToLbHr = (v) => v / C.kKgSPerLbHr;
const ftToM = (v) => v * C.kMPerFt;
const mToFt = (v) => v / C.kMPerFt;
const inToM = (v) => v * C.kMPerIn;
const mToIn = (v) => v / C.kMPerIn;
const cmToM = (v) => v * 0.01;
const mToCm = (v) => v * 100.0;
const ftLbToNm = (v) => v * C.kNmPerFtLb;
const nmToFtLb = (v) => v / C.kNmPerFtLb;
const rpmToRadS = (v) => v * (C.kTwoPi / 60.0);
const radSToRpm = (v) => v * (60.0 / C.kTwoPi);

function baroPaAtAltitudeM(altitudeM) {
  const h = clampFinite(altitudeM, -500.0, 11000.0);
  const ratio = 1.0 - 2.25577e-5 * h;
  return C.kAtmPa * Math.pow(ratio, 5.25588);
}

function baroPsiaAtAltitudeFt(altitudeFt) {
  const altM = clampFinite(ftToM(altitudeFt), -500.0, 20000.0);
  return paToPsia(baroPaAtAltitudeM(altM));
}

function airDensityRatioAtAltitudeFt(altitudeFt, tempF = 70.0) {
  const baro = baroPsiaAtAltitudeFt(altitudeFt);
  const tempR = clampFinite(fToR(tempF), 300.0, 1000.0);
  return (baro / C.kAtmPsia) * (529.67 / tempR);
}

  return { baroPaAtAltitudeM, baroPsiaAtAltitudeFt, airDensityRatioAtAltitudeFt, fToC, cToF, fToK, kToF, fToR, rToF, deltaFToDeltaK, deltaKToDeltaF, psiaToPa, paToPsia, psigToPsia, psiaToPsig, inHgVacToPsia, psiaToInHgVac, micronsToPa, paToMicrons, micronsToPsia, psiaToMicrons, inWCToPa, paToInWC, inWCToPsi, psiToInWC, ftWaterToPsi, psiToFtWater, barToPsia, psiaToBar, kPaToPsia, psiaToKPa, btuLbToJKg, jKgToBtuLb, btuLbRToJKgK, jKgKToBtuLbR, lbFt3ToKgM3, kgM3ToLbFt3, paSToCp, cpToPaS, wmKToBtuHrFtF, btuHrFtFToWmK, uValueIPToSI, uValueSIToIP, btuHrToWatts, wattsToBtuHr, tonsToBtuHr, btuHrToTons, tonsToKw, hpToWatts, wattsToHp, cfmToM3s, m3sToCfm, fpmToMs, msToFpm, gpmToM3s, m3sToGpm, lbHrToKgS, kgSToLbHr, ftToM, mToFt, inToM, mToIn, cmToM, mToCm, ftLbToNm, nmToFtLb, rpmToRadS, radSToRpm };
  })();

  _M.MathSolvers = (function() {
const { Complex, EPhysicsWarn, EStatusCode, lerpVal } = _M.Types;

function pchipSlopeAt(xs, ys, n, i) {
  const secant = (k) => {
    const dx = xs[k + 1] - xs[k];
    return Math.abs(dx) > 1e-15 ? (ys[k + 1] - ys[k]) / dx : 0.0;
  };
  if (n < 2) return 0.0;
  if (n === 2) return secant(0);
  if (i === 0) {
    const h0 = xs[1] - xs[0];
    const h1 = xs[2] - xs[1];
    const d0 = secant(0);
    const d1 = secant(1);
    let d = ((2.0 * h0 + h1) * d0 - h0 * d1) / Math.max(1e-15, h0 + h1);
    if (d * d0 <= 0.0) return 0.0;
    if (d0 * d1 <= 0.0 && Math.abs(d) > Math.abs(3.0 * d0)) d = 3.0 * d0;
    return d;
  }
  if (i === n - 1) {
    const h0 = xs[n - 1] - xs[n - 2];
    const h1 = xs[n - 2] - xs[n - 3];
    const d0 = secant(n - 2);
    const d1 = secant(n - 3);
    let d = ((2.0 * h0 + h1) * d0 - h0 * d1) / Math.max(1e-15, h0 + h1);
    if (d * d0 <= 0.0) return 0.0;
    if (d0 * d1 <= 0.0 && Math.abs(d) > Math.abs(3.0 * d0)) d = 3.0 * d0;
    return d;
  }
  const da = secant(i - 1);
  const db = secant(i);
  if (da * db <= 0.0) return 0.0;
  const h0 = xs[i] - xs[i - 1];
  const h1 = xs[i + 1] - xs[i];
  const w1 = 2.0 * h1 + h0;
  const w2 = h1 + 2.0 * h0;
  return (w1 + w2) / (w1 / da + w2 / db);
}

function findInterval(xs, count, x) {
  if (count <= 2) return 0;
  if (x <= xs[0]) return 0;
  if (x >= xs[count - 1]) return count - 2;
  let lo = 0;
  let hi = count - 2;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (x < xs[mid]) hi = mid - 1;
    else if (x > xs[mid + 1]) lo = mid + 1;
    else return mid;
  }
  return Math.max(0, Math.min(count - 2, lo));
}

function pchipEval(xs, ys, count, x) {
  if (count <= 0) return 0.0;
  if (count === 1) return ys[0];
  if (x <= xs[0]) return ys[0];
  if (x >= xs[count - 1]) return ys[count - 1];
  const k = findInterval(xs, count, x);
  const m0 = pchipSlopeAt(xs, ys, count, k);
  const m1 = pchipSlopeAt(xs, ys, count, k + 1);
  const h = xs[k + 1] - xs[k];
  if (Math.abs(h) <= 1e-15) return ys[k];
  const t = (x - xs[k]) / h;
  const t2 = t * t;
  const t3 = t2 * t;
  return (2 * t3 - 3 * t2 + 1) * ys[k] + (t3 - 2 * t2 + t) * h * m0 + (-2 * t3 + 3 * t2) * ys[k + 1] + (t3 - t2) * h * m1;
}

function pchipEvalOffset(xs, ys, yOffset, count, x) {
  if (count <= 0) return 0.0;
  if (count === 1) return ys[yOffset];
  if (x <= xs[0]) return ys[yOffset];
  if (x >= xs[count - 1]) return ys[yOffset + count - 1];
  // Slice-free evaluation using small view helper
  const row = ys.subarray(yOffset, yOffset + count);
  return pchipEval(xs, row, count, x);
}

function pchipEval2D(xs, nx, ys, ny, gridRowMajor, x, y) {
  if (nx <= 0 || ny <= 0) return 0.0;
  const ix = findInterval(xs, nx, x);
  const rowStart = Math.max(0, ix - 1);
  const rowEnd = Math.min(nx - 1, ix + 2);
  const subXs = [];
  const subVals = [];
  for (let r = rowStart; r <= rowEnd; ++r) {
    subXs.push(xs[r]);
    subVals.push(pchipEvalOffset(ys, gridRowMajor, r * ny, ny, y));
  }
  return pchipEval(subXs, subVals, subXs.length, x);
}

function brentSolve(fn, loIn, hiIn, tol = 1e-9, maxIter = 80) {
  let lo = loIn;
  let hi = hiIn;
  if (!Number.isFinite(lo) || !Number.isFinite(hi)) return { value: 0.0, status: EStatusCode.InvalidInput, residual: NaN };
  if (lo > hi) { const t = lo; lo = hi; hi = t; }
  let a = lo;
  let b = hi;
  let fa = fn(a);
  let fb = fn(b);
  if (!Number.isFinite(fa) || !Number.isFinite(fb)) return { value: a, status: EStatusCode.InvalidInput, residual: NaN };
  if (Math.abs(fa) <= 1e-15) return { value: a, status: EStatusCode.Ok, residual: Math.abs(fa) };
  if (Math.abs(fb) <= 1e-15) return { value: b, status: EStatusCode.Ok, residual: Math.abs(fb) };
  if (fa * fb > 0.0) {
    return Math.abs(fa) <= Math.abs(fb)
      ? { value: a, status: EStatusCode.OutOfRange, residual: Math.abs(fa) }
      : { value: b, status: EStatusCode.OutOfRange, residual: Math.abs(fb) };
  }
  const fScale = Math.max(1.0, Math.abs(fa), Math.abs(fb));
  let c = a;
  let fc = fa;
  let d = b - a;
  let e = d;
  const eps = 2.2204460492503131e-16;
  for (let iter = 0; iter < maxIter; ++iter) {
    if ((fb > 0 && fc > 0) || (fb < 0 && fc < 0)) {
      c = a; fc = fa; d = b - a; e = d;
    }
    if (Math.abs(fc) < Math.abs(fb)) {
      a = b; b = c; c = a;
      fa = fb; fb = fc; fc = fa;
    }
    const tol1 = 2.0 * eps * Math.abs(b) + 0.5 * tol;
    const xm = 0.5 * (c - b);
    if (Math.abs(xm) <= tol1 || Math.abs(fb) <= 1e-15) {
      return { value: b, status: Math.abs(fb) <= 1e-2 * fScale ? EStatusCode.Ok : EStatusCode.DidNotConverge, residual: Math.abs(fb) };
    }
    if (Math.abs(e) >= tol1 && Math.abs(fa) > Math.abs(fb)) {
      const s = fb / fa;
      let p = 0.0;
      let q = 0.0;
      if (a === c) {
        p = 2.0 * xm * s;
        q = 1.0 - s;
      } else {
        const qr = fa / fc;
        const r = fb / fc;
        p = s * (2.0 * xm * qr * (qr - r) - (b - a) * (r - 1.0));
        q = (qr - 1.0) * (r - 1.0) * (s - 1.0);
      }
      if (p > 0.0) q = -q;
      p = Math.abs(p);
      const min1 = 3.0 * xm * q - Math.abs(tol1 * q);
      const min2 = Math.abs(e * q);
      if (2.0 * p < (min1 < min2 ? min1 : min2)) {
        e = d; d = p / q;
      } else {
        d = xm; e = d;
      }
    } else {
      d = xm; e = d;
    }
    a = b; fa = fb;
    if (Math.abs(d) > tol1) b += d;
    else b += (xm >= 0.0 ? tol1 : -tol1);
    fb = fn(b);
    if (!Number.isFinite(fb)) return { value: a, status: EStatusCode.DidNotConverge, residual: Math.abs(fa) };
  }
  return { value: b, status: EStatusCode.DidNotConverge, residual: Math.abs(fb) };
}

function rk4Step(fn, t, dt, state) {
  const n = state.length;
  const k1 = fn(t, state);
  const tmp = new Float64Array(n);
  for (let i = 0; i < n; ++i) tmp[i] = state[i] + 0.5 * dt * k1[i];
  const k2 = fn(t + 0.5 * dt, tmp);
  for (let i = 0; i < n; ++i) tmp[i] = state[i] + 0.5 * dt * k2[i];
  const k3 = fn(t + 0.5 * dt, tmp);
  for (let i = 0; i < n; ++i) tmp[i] = state[i] + dt * k3[i];
  const k4 = fn(t + dt, tmp);
  for (let i = 0; i < n; ++i) {
    state[i] += (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
  }
}

function solveLinearComplexLU(A, B, n) {
  const m = A.map((z) => new Complex(z.re, z.im));
  const rhs = B.map((z) => new Complex(z.re, z.im));
  let matrixInfNorm = 0.0;
  for (let r = 0; r < n; ++r) {
    let rowSum = 0.0;
    let rowMax = 0.0;
    for (let c = 0; c < n; ++c) {
      const v = m[r * n + c].abs();
      rowSum += v;
      if (v > rowMax) rowMax = v;
    }
    if (rowSum > matrixInfNorm) matrixInfNorm = rowSum;
    if (rowMax <= 1e-18) return { status: EStatusCode.SingularCircuit, warnings: 0, solution: [], scaledResidual: Infinity, minPivotRatio: 0.0 };
    const inv = 1.0 / rowMax;
    for (let c = 0; c < n; ++c) m[r * n + c] = m[r * n + c].scale(inv);
    rhs[r] = rhs[r].scale(inv);
  }

  let maxPivot = 0.0;
  let minPivot = 1e300;
  for (let k = 0; k < n; ++k) {
    let pivotRow = k;
    let bestAbs = m[k * n + k].abs();
    for (let r = k + 1; r < n; ++r) {
      const v = m[r * n + k].abs();
      if (v > bestAbs) { bestAbs = v; pivotRow = r; }
    }
    if (bestAbs <= 1e-13) return { status: EStatusCode.SingularCircuit, warnings: 0, solution: [], scaledResidual: Infinity, minPivotRatio: 0.0 };
    if (bestAbs > maxPivot) maxPivot = bestAbs;
    if (bestAbs < minPivot) minPivot = bestAbs;

    if (pivotRow !== k) {
      for (let c = k; c < n; ++c) {
        const tmp = m[k * n + c];
        m[k * n + c] = m[pivotRow * n + c];
        m[pivotRow * n + c] = tmp;
      }
      const tr = rhs[k]; rhs[k] = rhs[pivotRow]; rhs[pivotRow] = tr;
    }
    const pivot = m[k * n + k];
    for (let r = k + 1; r < n; ++r) {
      const factor = m[r * n + k].div(pivot);
      if (factor.abs() === 0.0) continue;
      m[r * n + k] = new Complex(0.0, 0.0);
      for (let c = k + 1; c < n; ++c) {
        m[r * n + c] = m[r * n + c].sub(factor.mul(m[k * n + c]));
      }
      rhs[r] = rhs[r].sub(factor.mul(rhs[k]));
    }
  }

  const x = new Array(n);
  for (let i = n - 1; i >= 0; --i) {
    let sum = rhs[i];
    for (let c = i + 1; c < n; ++c) sum = sum.sub(m[i * n + c].mul(x[c]));
    x[i] = sum.div(m[i * n + i]);
    if (!Number.isFinite(x[i].re) || !Number.isFinite(x[i].im)) {
      return { status: EStatusCode.SingularCircuit, warnings: 0, solution: [], scaledResidual: Infinity, minPivotRatio: 0.0 };
    }
  }

  let maxRes = 0.0;
  let maxX = 0.0;
  let maxB = 0.0;
  for (let i = 0; i < n; ++i) {
    if (x[i].abs() > maxX) maxX = x[i].abs();
    if (B[i].abs() > maxB) maxB = B[i].abs();
    let ax = new Complex(0.0, 0.0);
    for (let c = 0; c < n; ++c) ax = ax.add(A[i * n + c].mul(x[c]));
    const err = ax.sub(B[i]).abs();
    if (err > maxRes) maxRes = err;
  }
  const scaledResidual = maxRes / Math.max(1e-18, matrixInfNorm * maxX + maxB);
  const minPivotRatio = maxPivot > 0.0 ? minPivot / maxPivot : 0.0;
  let warnings = 0;
  if (minPivotRatio < 1e-10) warnings |= EPhysicsWarn.WarnIllConditioned;
  const status = scaledResidual > 1e-6 ? EStatusCode.SingularCircuit : EStatusCode.Ok;
  return { status, warnings, solution: x, scaledResidual, minPivotRatio };
}

function pchipEvalUniform(x0, dx, ys, count, x) {
  if (count <= 0 || dx <= 0) return 0.0;
  const xs = new Float64Array(count);
  for (let i = 0; i < count; ++i) xs[i] = x0 + i * dx;
  return pchipEval(xs, ys, count, x);
}

function bilinearEval(xs, nx, ys, ny, gridRowMajor, x, y) {
  if (nx <= 0 || ny <= 0) return 0.0;
  const ix = findInterval(xs, nx, x);
  const iy = findInterval(ys, ny, y);
  const tx = nx > 1 ? Math.max(0, Math.min(1, (x - xs[ix]) / Math.max(1e-15, xs[ix + 1] - xs[ix]))) : 0.0;
  const ty = ny > 1 ? Math.max(0, Math.min(1, (y - ys[iy]) / Math.max(1e-15, ys[iy + 1] - ys[iy]))) : 0.0;
  const ix1 = Math.min(nx - 1, ix + 1), iy1 = Math.min(ny - 1, iy + 1);
  const v00 = gridRowMajor[ix * ny + iy], v01 = gridRowMajor[ix * ny + iy1];
  const v10 = gridRowMajor[ix1 * ny + iy], v11 = gridRowMajor[ix1 * ny + iy1];
  return lerpVal(lerpVal(v00, v01, ty), lerpVal(v10, v11, ty), tx);
}

class FixedStepAccumulator {
  constructor(fixedDt = 0.01, maxSubsteps = 16) {
    this.fixedDt = fixedDt;
    this.maxSubsteps = maxSubsteps;
    this.accumulator = 0.0;
    this.simTime = 0.0;
  }
  advance(frameDt) {
    if (!Number.isFinite(frameDt) || frameDt <= 0.0 || this.fixedDt <= 0.0) {
      return { numSubsteps: 0, actualDtAdvanced: 0.0, capped: false };
    }
    this.accumulator += frameDt;
    let numSubsteps = 0, actualDtAdvanced = 0.0, capped = false;
    while (this.accumulator + 1e-12 >= this.fixedDt && numSubsteps < this.maxSubsteps) {
      this.accumulator = Math.max(0.0, this.accumulator - this.fixedDt);
      this.simTime += this.fixedDt;
      ++numSubsteps;
      actualDtAdvanced += this.fixedDt;
    }
    if (this.accumulator >= this.fixedDt && numSubsteps >= this.maxSubsteps) {
      capped = true;
      this.accumulator = Math.min(this.accumulator, this.fixedDt * 0.5);
    }
    return { numSubsteps, actualDtAdvanced, capped };
  }
  reset() { this.accumulator = 0.0; this.simTime = 0.0; }
}

  return { findInterval, pchipEval, pchipEvalOffset, pchipEval2D, brentSolve, rk4Step, solveLinearComplexLU, pchipEvalUniform, bilinearEval, FixedStepAccumulator };
  })();

  _M.AdvancedSolvers = (function() {
// Pure JS advanced numerical solvers matching Core/AdvancedSolvers.cpp cleanly.
const { EStatusCode, EPhysicsWarn } = _M.Types;

function minimize1D(fn, lo, hi, tol = 1e-6, maxIter = 80) {
  if (typeof fn !== 'function' || !Number.isFinite(lo) || !Number.isFinite(hi) || !Number.isFinite(tol) || maxIter <= 0) {
    return { value: 0, status: EStatusCode.InvalidInput, warnings: EPhysicsWarn.WarnNone, residual: 0 };
  }
  let a = lo;
  let b = hi;
  let warnings = EPhysicsWarn.WarnNone;
  if (a > b) {
    const tmp = a;
    a = b;
    b = tmp;
    warnings |= EPhysicsWarn.WarnClamped;
  }
  const useTol = Math.max(1e-12, tol);
  if (b - a <= useTol) {
    const mid = 0.5 * (a + b);
    const fMid = fn(mid);
    if (!Number.isFinite(fMid)) {
      return { value: 0, status: EStatusCode.OutOfRange, warnings, residual: 0 };
    }
    return { value: mid, status: EStatusCode.Ok, warnings, residual: fMid };
  }

  const c = 0.38196601125010515;
  const sqrtEps = 1.4901161193847656e-8;
  let x = a + c * (b - a);
  let w = x;
  let v = x;
  let fx = fn(x);
  if (!Number.isFinite(fx)) {
    return { value: 0, status: EStatusCode.OutOfRange, warnings, residual: 0 };
  }
  let fw = fx;
  let fv = fx;
  let d = 0.0;
  let e = 0.0;
  let converged = false;

  for (let iter = 0; iter < maxIter; iter++) {
    const xm = 0.5 * (a + b);
    const tol1 = sqrtEps * Math.abs(x) + useTol / 3.0;
    const tol2 = 2.0 * tol1;
    if (Math.abs(x - xm) <= tol2 - 0.5 * (b - a)) {
      converged = true;
      break;
    }

    let p = 0.0;
    let q = 0.0;
    let r = 0.0;
    if (Math.abs(e) > tol1) {
      r = (x - w) * (fx - fv);
      q = (x - v) * (fx - fw);
      p = (x - v) * q - (x - w) * r;
      q = 2.0 * (q - r);
      if (q > 0.0) p = -p;
      q = Math.abs(q);
      r = e;
      e = d;
    }

    if (Math.abs(e) > tol1 && Math.abs(p) < Math.abs(0.5 * q * r) && p > q * (a - x) && p < q * (b - x)) {
      d = p / q;
      const uTest = x + d;
      if ((uTest - a) < tol2 || (b - uTest) < tol2) {
        d = (x < xm) ? tol1 : -tol1;
      }
    } else {
      e = (x < xm) ? (b - x) : (a - x);
      d = c * e;
    }

    const u = (Math.abs(d) >= tol1) ? (x + d) : (x + ((d > 0.0) ? tol1 : -tol1));
    const fu = fn(u);
    if (!Number.isFinite(fu)) {
      return { value: x, status: EStatusCode.OutOfRange, warnings, residual: fx };
    }

    if (fu <= fx) {
      if (u < x) b = x;
      else a = x;
      v = w; fv = fw;
      w = x; fw = fx;
      x = u; fx = fu;
    } else {
      if (u < x) a = u;
      else b = u;
      if (fu <= fw || w === x) {
        v = w; fv = fw;
        w = u; fw = fu;
      } else if (fu <= fv || v === x || v === w) {
        v = u; fv = fu;
      }
    }
  }

  const fLo = fn(lo);
  const fHi = fn(hi);
  if (Number.isFinite(fLo) && fLo < fx) { x = lo; fx = fLo; }
  if (Number.isFinite(fHi) && fHi < fx) { x = hi; fx = fHi; }

  return {
    value: x,
    status: converged ? EStatusCode.Ok : EStatusCode.DidNotConverge,
    warnings,
    residual: fx,
  };
}

function gaussLegendreIntegrate(fn, a, b, panels = 4) {
  if (typeof fn !== 'function' || !Number.isFinite(a) || !Number.isFinite(b)) {
    return { value: 0, status: EStatusCode.InvalidInput, warnings: EPhysicsWarn.WarnNone, residual: 0 };
  }
  if (a === b) {
    return { value: 0, status: EStatusCode.Ok, warnings: EPhysicsWarn.WarnNone, residual: 0 };
  }
  const nodes = [
    -0.906179845938663992798,
    -0.538469310105683091036,
    0.0,
    0.538469310105683091036,
    0.906179845938663992798,
  ];
  const weights = [
    0.236926885056189087514,
    0.478628670499366468041,
    0.568888888888888888889,
    0.478628670499366468041,
    0.236926885056189087514,
  ];
  const reqPanels = Math.trunc(panels);
  const clampedPanels = Math.max(1, Math.min(256, reqPanels));
  const warnings = (clampedPanels !== reqPanels) ? EPhysicsWarn.WarnClamped : EPhysicsWarn.WarnNone;
  const h = (b - a) / clampedPanels;
  const halfH = 0.5 * h;
  let total = 0.0;

  for (let p = 0; p < clampedPanels; p++) {
    const subA = a + p * h;
    const mid = subA + halfH;
    let panelSum = 0.0;
    for (let k = 0; k < 5; k++) {
      const fx = fn(mid + halfH * nodes[k]);
      if (!Number.isFinite(fx)) {
        return { value: 0, status: EStatusCode.OutOfRange, warnings, residual: 0 };
      }
      panelSum += weights[k] * fx;
    }
    total += halfH * panelSum;
  }
  return { value: total, status: EStatusCode.Ok, warnings, residual: 0 };
}

function solveLinearRealLU(A, B, n) {
  if (!A || !B || n <= 0 || A.length !== n * n || B.length !== n) {
    return {
      status: EStatusCode.InvalidInput,
      warnings: EPhysicsWarn.WarnNone,
      residual: 0,
      value: { solution: [], scaledResidual: 0, minPivotRatio: 0 },
    };
  }

  const M = new Float64Array(n * n);
  const rhs = new Float64Array(n);
  for (let i = 0; i < n * n; i++) {
    if (!Number.isFinite(A[i])) {
      return {
        status: EStatusCode.InvalidInput,
        warnings: EPhysicsWarn.WarnNone,
        residual: 0,
        value: { solution: [], scaledResidual: 0, minPivotRatio: 0 },
      };
    }
    M[i] = A[i];
  }
  for (let i = 0; i < n; i++) {
    if (!Number.isFinite(B[i])) {
      return {
        status: EStatusCode.InvalidInput,
        warnings: EPhysicsWarn.WarnNone,
        residual: 0,
        value: { solution: [], scaledResidual: 0, minPivotRatio: 0 },
      };
    }
    rhs[i] = B[i];
  }

  let matrixInfNorm = 0.0;
  for (let r = 0; r < n; r++) {
    let rowSum = 0.0;
    let rowMax = 0.0;
    for (let c = 0; c < n; c++) {
      const v = Math.abs(M[r * n + c]);
      rowSum += v;
      if (v > rowMax) rowMax = v;
    }
    if (rowSum > matrixInfNorm) matrixInfNorm = rowSum;
    if (rowMax <= 1e-18) {
      return {
        status: EStatusCode.SingularCircuit,
        warnings: EPhysicsWarn.WarnNone,
        residual: 0,
        value: { solution: [], scaledResidual: 0, minPivotRatio: 0 },
      };
    }
    const scale = 1.0 / rowMax;
    for (let c = 0; c < n; c++) M[r * n + c] *= scale;
    rhs[r] *= scale;
  }

  let maxPivot = 0.0;
  let minPivot = 1e300;
  for (let k = 0; k < n; k++) {
    let pivotRow = k;
    let bestAbs = Math.abs(M[k * n + k]);
    for (let r = k + 1; r < n; r++) {
      const v = Math.abs(M[r * n + k]);
      if (v > bestAbs) {
        bestAbs = v;
        pivotRow = r;
      }
    }
    if (bestAbs <= 1e-14) {
      return {
        status: EStatusCode.SingularCircuit,
        warnings: EPhysicsWarn.WarnNone,
        residual: 0,
        value: { solution: [], scaledResidual: 0, minPivotRatio: 0 },
      };
    }
    if (bestAbs > maxPivot) maxPivot = bestAbs;
    if (bestAbs < minPivot) minPivot = bestAbs;

    if (pivotRow !== k) {
      for (let c = k; c < n; c++) {
        const tmp = M[k * n + c];
        M[k * n + c] = M[pivotRow * n + c];
        M[pivotRow * n + c] = tmp;
      }
      const tr = rhs[k];
      rhs[k] = rhs[pivotRow];
      rhs[pivotRow] = tr;
    }

    const pivot = M[k * n + k];
    for (let r = k + 1; r < n; r++) {
      const factor = M[r * n + k] / pivot;
      if (factor === 0.0) continue;
      M[r * n + k] = 0.0;
      for (let c = k + 1; c < n; c++) {
        M[r * n + c] -= factor * M[k * n + c];
      }
      rhs[r] -= factor * rhs[k];
    }
  }

  const sol = new Array(n).fill(0.0);
  for (let i = n - 1; i >= 0; i--) {
    let sum = rhs[i];
    for (let c = i + 1; c < n; c++) {
      sum -= M[i * n + c] * sol[c];
    }
    sol[i] = sum / M[i * n + i];
    if (!Number.isFinite(sol[i])) {
      return {
        status: EStatusCode.SingularCircuit,
        warnings: EPhysicsWarn.WarnNone,
        residual: 0,
        value: { solution: [], scaledResidual: 0, minPivotRatio: 0 },
      };
    }
  }

  let maxRes = 0.0;
  let maxX = 0.0;
  let maxB = 0.0;
  for (let i = 0; i < n; i++) {
    if (Math.abs(sol[i]) > maxX) maxX = Math.abs(sol[i]);
    if (Math.abs(B[i]) > maxB) maxB = Math.abs(B[i]);
    let ax = 0.0;
    for (let c = 0; c < n; c++) ax += A[i * n + c] * sol[c];
    const err = Math.abs(ax - B[i]);
    if (err > maxRes) maxRes = err;
  }
  const denom = Math.max(1e-18, matrixInfNorm * maxX + maxB);
  const scaledRes = maxRes / denom;
  const pivotRatio = (maxPivot > 0.0) ? (minPivot / maxPivot) : 0.0;
  let warnings = EPhysicsWarn.WarnNone;
  if (pivotRatio < 1e-10) warnings |= EPhysicsWarn.WarnIllConditioned;
  const status = (scaledRes > 1e-6) ? EStatusCode.SingularCircuit : EStatusCode.Ok;
  return {
    status,
    warnings,
    residual: scaledRes,
    value: { solution: sol, scaledResidual: scaledRes, minPivotRatio: pivotRatio },
  };
}

function newtonSolveMulti(fn, initialX, maxIter = 40, tol = 1e-8) {
  const n = Array.isArray(initialX) ? initialX.length : 0;
  if (typeof fn !== 'function' || n <= 0 || n > 512 || maxIter <= 0 || !Number.isFinite(tol)) {
    return {
      status: EStatusCode.InvalidInput,
      warnings: EPhysicsWarn.WarnNone,
      residual: 0,
      value: { solution: [], iterations: 0, maxResidual: 0 },
    };
  }
  const x = initialX.map(Number);
  if (x.some((v) => !Number.isFinite(v))) {
    return {
      status: EStatusCode.InvalidInput,
      warnings: EPhysicsWarn.WarnNone,
      residual: 0,
      value: { solution: [], iterations: 0, maxResidual: 0 },
    };
  }

  const normInf = (vec) => {
    let m = 0.0;
    for (const v of vec) {
      if (!Number.isFinite(v)) return 1e300;
      const a = Math.abs(v);
      if (a > m) m = a;
    }
    return m;
  };
  const norm2Sq = (vec) => {
    let s = 0.0;
    for (const v of vec) {
      if (!Number.isFinite(v)) return 1e300;
      s += v * v;
    }
    return s;
  };

  let F = fn(x);
  if (!F || F.length !== n) {
    return {
      status: EStatusCode.OutOfRange,
      warnings: EPhysicsWarn.WarnNone,
      residual: 0,
      value: { solution: x, iterations: 0, maxResidual: 0 },
    };
  }
  let curInf = normInf(F);
  let curNormSq = norm2Sq(F);
  if (curInf <= tol) {
    return {
      status: EStatusCode.Ok,
      warnings: EPhysicsWarn.WarnNone,
      residual: curInf,
      value: { solution: x, iterations: 0, maxResidual: curInf },
    };
  }

  const jac = new Array(n * n).fill(0.0);
  const negF = new Array(n).fill(0.0);
  let iterDone = 0;

  for (let iter = 0; iter < maxIter; iter++) {
    iterDone = iter + 1;
    const xWork = x.slice();
    for (let j = 0; j < n; j++) {
      const xSave = xWork[j];
      const h = 1e-7 * Math.max(1.0, Math.abs(xSave));
      xWork[j] = xSave + h;
      const fPert = fn(xWork);
      xWork[j] = xSave;
      if (!fPert || fPert.length !== n) {
        return {
          status: EStatusCode.OutOfRange,
          warnings: EPhysicsWarn.WarnNone,
          residual: curInf,
          value: { solution: x, iterations: iterDone, maxResidual: curInf },
        };
      }
      for (let i = 0; i < n; i++) {
        jac[i * n + j] = (fPert[i] - F[i]) / h;
      }
    }

    for (let i = 0; i < n; i++) negF[i] = -F[i];
    const lin = solveLinearRealLU(jac, negF, n);
    if (lin.status !== EStatusCode.Ok) {
      return {
        status: EStatusCode.SingularCircuit,
        warnings: EPhysicsWarn.WarnNone,
        residual: curInf,
        value: { solution: x, iterations: iterDone, maxResidual: curInf },
      };
    }
    const dx = lin.value.solution;

    let alpha = 1.0;
    let accepted = false;
    let xNext = x.slice();
    let fNext = null;
    let nextInf = curInf;
    let nextNormSq = curNormSq;

    for (let ls = 0; ls < 10; ls++) {
      for (let i = 0; i < n; i++) xNext[i] = x[i] + alpha * dx[i];
      fNext = fn(xNext);
      if (fNext && fNext.length === n) {
        nextInf = normInf(fNext);
        nextNormSq = norm2Sq(fNext);
        if (nextNormSq <= (1.0 - 1e-4 * alpha) * curNormSq || nextInf < curInf) {
          accepted = true;
          break;
        }
      }
      alpha *= 0.5;
    }

    if (!accepted) {
      for (let i = 0; i < n; i++) xNext[i] = x[i] + alpha * dx[i];
      fNext = fn(xNext);
      if (!fNext || fNext.length !== n) {
        return {
          status: EStatusCode.DidNotConverge,
          warnings: EPhysicsWarn.WarnNone,
          residual: curInf,
          value: { solution: x, iterations: iterDone, maxResidual: curInf },
        };
      }
      nextInf = normInf(fNext);
      nextNormSq = norm2Sq(fNext);
    }

    for (let i = 0; i < n; i++) x[i] = xNext[i];
    F = fNext;
    curInf = nextInf;
    curNormSq = nextNormSq;

    if (curInf <= tol) {
      return {
        status: EStatusCode.Ok,
        warnings: EPhysicsWarn.WarnNone,
        residual: curInf,
        value: { solution: x, iterations: iterDone, maxResidual: curInf },
      };
    }
  }

  return {
    status: EStatusCode.DidNotConverge,
    warnings: EPhysicsWarn.WarnNone,
    residual: curInf,
    value: { solution: x, iterations: iterDone, maxResidual: curInf },
  };
}

  return { minimize1D, gaussLegendreIntegrate, solveLinearRealLU, newtonSolveMulti };
  })();

  _M.Electrical = (function() {
const C = _M.Constants;
const { Complex, clampFinite, safeDiv } = _M.Types;

const inductiveReactance = (inductanceH, freqHz = C.kGridFreqHz) =>
  C.kTwoPi * Math.max(0.0, freqHz) * Math.max(0.0, inductanceH);

const capacitiveReactance = (capacitanceUf, freqHz = C.kGridFreqHz) =>
  freqHz <= 1e-9 ? 1e12 : 1.0 / (C.kTwoPi * freqHz * Math.max(1e-12, capacitanceUf * 1e-6));

function parallelImpedance(z1, z2) {
  const sum = z1.add(z2);
  return sum.abs() < 1e-12 ? new Complex(1e12, 0.0) : z1.mul(z2).div(sum);
}

function calcPowerTriangle(voltageRms, currentRms, pfAngleDeg) {
  const s = Math.max(0.0, voltageRms) * Math.max(0.0, currentRms);
  const rad = pfAngleDeg * (C.kPi / 180.0);
  return {
    realPowerW: s * Math.cos(rad), reactivePowerVar: s * Math.sin(rad),
    apparentPowerVa: s, powerFactor: Math.cos(rad), phaseAngleDeg: pfAngleDeg,
  };
}

function pfCorrectionCapacitanceUf(realPowerW, voltageRms, currentPf, targetPf, freqHz = C.kGridFreqHz) {
  const p = Math.max(0.0, realPowerW), v = Math.max(1.0, voltageRms), f = Math.max(1.0, freqHz);
  const pf1 = clampFinite(currentPf, 0.1, 0.9999), pf2 = clampFinite(targetPf, pf1, 1.0);
  const qc = p * (Math.tan(Math.acos(pf1)) - Math.tan(Math.acos(pf2)));
  return Math.max(0.0, (qc / (C.kTwoPi * f * v * v)) * 1e6);
}

const liveRunCapacitorUf = (capCurrentA, capVoltageV, freqHz = C.kGridFreqHz) =>
  (1e6 * Math.max(0.0, capCurrentA)) / (C.kTwoPi * Math.max(1.0, freqHz) * Math.max(0.1, capVoltageV));

function calcThreePhase(lineToLineV, lineCurrentA, powerFactor, isDelta) {
  const vll = Math.max(0.0, lineToLineV), il = Math.max(0.0, lineCurrentA), pf = clampFinite(powerFactor, 0.0, 1.0);
  const s = C.kSqrt3 * vll * il;
  return {
    lineToLineV: vll, lineToNeutralV: vll / C.kSqrt3, lineCurrentA: il,
    phaseCurrentA: isDelta ? il / C.kSqrt3 : il,
    totalRealPowerW: s * pf, totalApparentVa: s, totalReactiveVar: s * Math.sqrt(Math.max(0.0, 1.0 - pf * pf)),
  };
}

function evaluateThreePhaseUnbalance(vab, vbc, vca) {
  const avg = (vab + vbc + vca) / 3.0;
  const maxDev = Math.max(Math.abs(vab - avg), Math.abs(vbc - avg), Math.abs(vca - avg));
  const unbPct = avg > 1.0 ? (maxDev / avg) * 100.0 : 0.0;
  const derate = unbPct <= 1.0 ? 1.0 : clampFinite(1.0 - 0.055 * (unbPct - 1.0) - 0.002 * (unbPct - 1.0) ** 2, 0.50, 1.0);
  return { avgVoltage: avg, maxDeviationV: maxDev, unbalancePct: unbPct, motorDeratingFactor: derate, approxTempRiseIncreasePct: 2.0 * unbPct * unbPct };
}

const AWG_TABLE = [
  { awg: 18, r: 7.77, x: 0.068, cu: 7, al: 0 }, { awg: 16, r: 4.89, x: 0.064, cu: 10, al: 0 },
  { awg: 14, r: 3.07, x: 0.058, cu: 15, al: 0 }, { awg: 12, r: 1.93, x: 0.054, cu: 20, al: 15 },
  { awg: 10, r: 1.21, x: 0.050, cu: 30, al: 25 }, { awg: 8, r: 0.764, x: 0.052, cu: 50, al: 40 },
  { awg: 6, r: 0.491, x: 0.051, cu: 65, al: 50 }, { awg: 4, r: 0.308, x: 0.048, cu: 85, al: 65 },
  { awg: 3, r: 0.245, x: 0.047, cu: 100, al: 75 }, { awg: 2, r: 0.194, x: 0.045, cu: 115, al: 90 },
  { awg: 1, r: 0.154, x: 0.046, cu: 130, al: 100 }, { awg: 0, r: 0.122, x: 0.044, cu: 150, al: 120 },
  { awg: -1, r: 0.0967, x: 0.043, cu: 175, al: 135 }, { awg: -2, r: 0.0766, x: 0.042, cu: 200, al: 155 },
  { awg: -3, r: 0.0608, x: 0.041, cu: 230, al: 180 },
  { awg: -4, r: 0.0497, x: 0.041, cu: 255, al: 205 },
  { awg: -5, r: 0.0415, x: 0.041, cu: 285, al: 230 },
  { awg: -6, r: 0.0356, x: 0.040, cu: 310, al: 250 },
  { awg: -7, r: 0.0312, x: 0.040, cu: 335, al: 270 },
  { awg: -8, r: 0.0250, x: 0.039, cu: 380, al: 310 },
];

function calcVoltageDrop(awgIndex, aluminum, sourceV, loadAmps, oneWayFt, threePhase = false, tempC = 75.0, pf = 0.90, ambientTempC = 30.0) {
  let mapped = awgIndex;
  if (awgIndex >= 475) mapped = -8;
  else if (awgIndex >= 375) mapped = -7;
  else if (awgIndex >= 325) mapped = -6;
  else if (awgIndex >= 275) mapped = -5;
  else if (awgIndex >= 225) mapped = -4;

  let found = AWG_TABLE[3], best = 1e9;
  for (const e of AWG_TABLE) { const d = Math.abs(e.awg - mapped); if (d < best) { best = d; found = e; } }
  const rPerKft = found.r * (aluminum ? 1.64 : 1.0) * Math.max(0.5, 1.0 + (aluminum ? 0.00403 : 0.00393) * (tempC - 75.0));
  const xPerKft = found.x;
  const pfSafe = clampFinite(pf, 0.5, 1.0);
  const sinPhi = Math.sqrt(Math.max(0.0, 1.0 - pfSafe * pfSafe));
  const zEffPerKft = rPerKft * pfSafe + xPerKft * sinPhi;
  const loopOhms = (threePhase ? C.kSqrt3 : 2.0) * zEffPerKft * (Math.max(0.0, oneWayFt) / 1000.0);
  const vDrop = loopOhms * Math.max(0.0, loadAmps);
  const pct = safeDiv(vDrop, Math.max(1.0, sourceV), 0.0) * 100.0;
  const baseAmp75 = aluminum ? found.al : found.cu;
  const derate = clampFinite(Math.sqrt(Math.max(0.0, (75.0 - ambientTempC) / 45.0)), 0.0, 1.15);
  return {
    conductorResOhmsPer1000Ft: rPerKft, conductorReactanceOhmsPer1000Ft: xPerKft,
    totalLoopOhms: loopOhms, voltageDropV: vDrop,
    voltageDropPct: pct, loadVoltageV: Math.max(0.0, sourceV - vDrop),
    necAmpacity75C: baseAmp75, deratedAmpacityA: Math.floor(baseAmp75 * derate + 1e-6),
    exceeds3Pct: pct > 3.0,
  };
}

function calcNec440McaMocp(compRla, fanFla, blowerFla, auxHeaterKw = 0.0, supplyV = 240.0, threePhaseHeater = false) {
  const c = Math.max(0, compRla), f = Math.max(0, fanFla), b = Math.max(0, blowerFla);
  const vDiv = Math.max(120.0, supplyV) * (threePhaseHeater ? C.kSqrt3 : 1.0);
  const h = safeDiv(Math.max(0, auxHeaterKw) * 1000.0, vDiv, 0.0);
  const largest = Math.max(c, f, b), others = (c + f + b) - largest;
  const mcaAmps = 1.25 * largest + others + 1.25 * h;
  const nominalMocp175A = c > 0 ? (1.75 * largest + others + 1.25 * h) : mcaAmps;
  const maxMocpAmps = c > 0 ? (2.25 * largest + others + 1.25 * h) : mcaAmps;
  const breakers = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600];
  let std = 15;
  for (const br of breakers) if (br <= maxMocpAmps + 1e-6) std = br;
  if (std < mcaAmps) for (const br of breakers) if (br >= mcaAmps) { std = br; break; }
  return { mcaAmps, maxMocpAmps, nominalMocp175A, standardBreakerAmps: std };
}

  return { parallelImpedance, calcPowerTriangle, pfCorrectionCapacitanceUf, calcThreePhase, evaluateThreePhaseUnbalance, calcVoltageDrop, calcNec440McaMocp, inductiveReactance, capacitiveReactance, liveRunCapacitorUf };
  })();

  _M.MotorsAndLoads = (function() {
const C = _M.Constants;
const { clampFinite, safeDiv } = _M.Types;

const EMotorKind = Object.freeze({
  PSC: 0, CSIR: 1, CSCR: 2, ShadedPole: 3, ECM: 4, ThreePhaseInduction: 5, VfdDriven: 6,
});

const EMotorFaultKind = Object.freeze({
  None: 0, OpenRunCapacitor: 1, WeakRunCapacitor: 2, OpenStartCapacitor: 3,
  StuckPotentialRelay: 4, LockedRotor: 5, SinglePhasing3Ph: 6, LowSupplyVoltage: 7,
});

function evaluateMotorPoint(spec, appliedV, loadTorqueFrac, fault = EMotorFaultKind.None, freqOverride = -1.0) {
  const kind = spec.kind ?? EMotorKind.PSC;
  const baseFreq = Math.max(1.0, spec.freqHz ?? 60.0);
  const freq = freqOverride > 0 ? freqOverride : baseFreq;
  const poles = Math.max(2, spec.poles ?? 4);
  const syncRpm = (120.0 * freq) / poles;
  const baseSyncRpm = (120.0 * baseFreq) / poles;
  const vRated = Math.max(12.0, spec.ratedVoltageV ?? 240.0);
  const effVoltageV = (fault === EMotorFaultKind.LowSupplyVoltage && appliedV >= vRated * 0.92)
    ? (appliedV * 0.85)
    : Math.max(0.0, appliedV);
  const vRatio = effVoltageV / vRated;
  const loadFrac = clampFinite(loadTorqueFrac, 0.0, 2.0);
  const ratedHp = spec.ratedHp ?? 0.5, fla = spec.fla ?? 3.2, lra = spec.lra ?? 15.0;
  const ratedEff = spec.ratedEff ?? 0.78, ratedPf = spec.ratedPf ?? 0.92;
  const ratedSlip = kind === EMotorKind.ECM ? 0.0 : (kind === EMotorKind.ShadedPole ? 0.12 : 0.042);
  const is3Ph = kind === EMotorKind.ThreePhaseInduction || kind === EMotorKind.VfdDriven;

  if (effVoltageV <= 1.0 || (kind === EMotorKind.ECM && vRatio < 0.45)) {
    return { syncRpm, shaftRpm: 0, slip: 1, torqueFtLb: 0, shaftHp: 0, lineCurrentA: 0, inputPowerW: 0, powerFactor: 0, efficiency: 0, thermalOverloadTripRisk: false, wouldFailToStart: true };
  }
  if (fault === EMotorFaultKind.LockedRotor) {
    const i = lra * vRatio;
    return { syncRpm, shaftRpm: 0, slip: 1, torqueFtLb: 0, shaftHp: 0, lineCurrentA: i, inputPowerW: effVoltageV * i * 0.45 * (is3Ph ? C.kSqrt3 : 1), powerFactor: 0.45, efficiency: 0, thermalOverloadTripRisk: true, wouldFailToStart: true };
  }
  if (fault === EMotorFaultKind.OpenStartCapacitor && (kind === EMotorKind.CSIR || kind === EMotorKind.CSCR) && loadFrac > 0.25) {
    const i = lra * 0.85 * vRatio;
    return { syncRpm, shaftRpm: 0, slip: 1, torqueFtLb: 0, shaftHp: 0, lineCurrentA: i, inputPowerW: effVoltageV * i * 0.45, powerFactor: 0.45, efficiency: 0, thermalOverloadTripRisk: true, wouldFailToStart: true };
  }
  if (fault === EMotorFaultKind.OpenRunCapacitor && (kind === EMotorKind.PSC || kind === EMotorKind.CSCR)) {
    if (kind === EMotorKind.PSC) {
      const i = lra * 0.72 * vRatio;
      return { syncRpm, shaftRpm: 0, slip: 1, torqueFtLb: 0, shaftHp: 0, lineCurrentA: i, inputPowerW: effVoltageV * i * 0.50, powerFactor: 0.50, efficiency: 0, thermalOverloadTripRisk: true, wouldFailToStart: true };
    }
    const slip = clampFinite(ratedSlip * 1.8 * loadFrac, 0.01, 0.25);
    const shaftRpm = syncRpm * (1.0 - slip);
    const baseRatedRpm = Math.max(1.0, baseSyncRpm * (1.0 - ratedSlip));
    const shaftHp = ratedHp * loadFrac * (shaftRpm / baseRatedRpm);
    const lineCurrentA = fla * (0.35 + 1.05 * loadFrac) / Math.max(0.4, vRatio);
    const pf = clampFinite(ratedPf * 0.72, 0.40, 0.90);
    const pIn = effVoltageV * lineCurrentA * pf;
    return { syncRpm, shaftRpm, slip, torqueFtLb: safeDiv(shaftHp * 5252, Math.max(1.0, shaftRpm), 0), shaftHp, lineCurrentA, inputPowerW: pIn, powerFactor: pf, efficiency: safeDiv(shaftHp * C.kWattsPerHp, pIn, 0), thermalOverloadTripRisk: lineCurrentA > fla * 1.25, wouldFailToStart: false };
  }
  if (fault === EMotorFaultKind.SinglePhasing3Ph) {
    const i = lra * 0.866 * vRatio;
    return { syncRpm, shaftRpm: 0, slip: 1, torqueFtLb: 0, shaftHp: 0, lineCurrentA: i, inputPowerW: effVoltageV * i * 0.48, powerFactor: 0.48, efficiency: 0, thermalOverloadTripRisk: true, wouldFailToStart: true };
  }

  const capFactor = fault === EMotorFaultKind.WeakRunCapacitor ? 0.82 : 1.0;
  const vFluxRatio = kind === EMotorKind.VfdDriven ? Math.max(vRatio, 0.85) : vRatio;
  if (loadFrac > vFluxRatio * vFluxRatio * capFactor * 2.2 && kind !== EMotorKind.ECM) {
    const i = lra * vRatio;
    return { syncRpm, shaftRpm: 0, slip: 1, torqueFtLb: 0, shaftHp: 0, lineCurrentA: i, inputPowerW: effVoltageV * i * 0.45 * (is3Ph ? C.kSqrt3 : 1), powerFactor: 0.45, efficiency: 0, thermalOverloadTripRisk: true, wouldFailToStart: true };
  }
  const vScaleSlip = kind === EMotorKind.ECM
    ? 0.0
    : (kind === EMotorKind.VfdDriven ? (baseFreq / Math.max(5.0, freq)) : (1.0 / Math.max(0.25, vRatio * vRatio * capFactor)));
  const slip = clampFinite(ratedSlip * loadFrac * vScaleSlip, 0.0, 0.30);
  const shaftRpm = syncRpm * (1.0 - slip);
  const baseRatedRpm = Math.max(1.0, baseSyncRpm * (1.0 - ratedSlip));
  const shaftHp = ratedHp * loadFrac * (shaftRpm / baseRatedRpm);
  const eff = clampFinite(ratedEff * (0.65 + 0.35 * Math.min(1.0, loadFrac / 0.75)) * (fault === EMotorFaultKind.WeakRunCapacitor ? 0.88 : 1.0), 0.25, 0.96);
  const coreScale = kind === EMotorKind.VfdDriven ? clampFinite(freq / baseFreq, 0.2, 1.5) : 1.0;
  const inputPowerW = (shaftHp * C.kWattsPerHp) / eff + ratedHp * 45.0 * coreScale;
  const pf = clampFinite(ratedPf * (0.45 + 0.55 * Math.min(1.0, loadFrac)), 0.35, 0.99);
  let lineCurrentA = inputPowerW / Math.max(1.0, effVoltageV * pf * (is3Ph ? C.kSqrt3 : 1.0));
  let trip = false;
  if (fault === EMotorFaultKind.StuckPotentialRelay) { lineCurrentA += lra * 0.45 * vRatio; trip = true; }
  return {
    syncRpm, shaftRpm, slip, torqueFtLb: safeDiv(shaftHp * 5252.0, Math.max(1.0, shaftRpm), 0.0),
    shaftHp, lineCurrentA, inputPowerW, powerFactor: pf, efficiency: eff,
    thermalOverloadTripRisk: trip || lineCurrentA > fla * 1.15, wouldFailToStart: false,
  };
}

function checkCompressorWindings(rcs, rcr, rsr, megohms, tempF, nomRcr = -1.0) {
  const sumErrorOhms = Math.abs((rcs + rcr) - rsr);
  const maxR = Math.max(rcs, rcr, rsr);
  const openWinding = rcs > 1e5 || rcr > 1e5 || rsr > 1e5 || rcs <= 0 || rcr <= 0;
  const kt = Math.pow(2.0, ((tempF - 32.0) * (5.0 / 9.0) - 40.0) / 10.0);
  const meg40 = Math.max(0.0, megohms) * kt;
  return {
    rcsOhms: rcs, rcrOhms: rcr, rsrOhms: rsr, sumErrorOhms,
    sumRuleValid: !openWinding && sumErrorOhms <= Math.max(0.25, maxR * 0.08),
    openWinding, shortedTurns: nomRcr > 0.1 && !openWinding && rcr < nomRcr * 0.80,
    grounded: meg40 < 5.0, megohmCorrectedAt40C: meg40,
  };
}

const stripHeatActualWatts = (ratedW, ratedV, actualV) => Math.max(0.0, ratedW) * (Math.max(0.0, actualV) / Math.max(1.0, ratedV)) ** 2;

function controlTransformerSecondaryV(priV, ratedPriV, ratedSecV, ratedVa, loadVa, loadPf = 0.85) {
  const oc = Math.max(0.0, priV) * (ratedSecV / Math.max(1.0, ratedPriV));
  const pf = clampFinite(loadPf, 0.2, 1.0);
  const sinPhi = Math.sqrt(Math.max(0.0, 1.0 - pf * pf));
  const regPu = 0.04 * pf + 0.07 * sinPhi;
  return Math.max(0.0, oc * (1.0 - regPu * (Math.max(0.0, loadVa) / Math.max(1.0, ratedVa))));
}

function flameRectificationMicroAmps(secVrms, flameMohms, groundRatio = 4.0, dirtyRod = false) {
  return ((0.45 * Math.max(0.0, secVrms)) / (Math.max(1.0, flameMohms) * (dirtyRod ? 2.5 : 1.0)))
    * clampFinite(groundRatio / 4.0, 0.05, 1.0) * (dirtyRod ? 0.25 : 1.0);
}

  return { evaluateMotorPoint, checkCompressorWindings, controlTransformerSecondaryV, flameRectificationMicroAmps, EMotorKind, EMotorFaultKind, stripHeatActualWatts };
  })();

  _M.CircuitSolver = (function() {
const C = _M.Constants;
const { Complex, EPhysicsWarn, EStatusCode, polarComplex } = _M.Types;
const { solveLinearComplexLU } = _M.MathSolvers;

const EMnaElementKind = Object.freeze({
  Resistor: 0, Capacitor: 1, Inductor: 2, ComplexImpedance: 3,
  VoltageSource: 4, CurrentSource: 5, Switch: 6, Transformer: 7, DiodeRectifier: 8,
});

class UnionFind {
  constructor(n) {
    this.p = new Int32Array(n);
    for (let i = 0; i < n; ++i) this.p[i] = i;
  }
  find(x) {
    while (this.p[x] !== x) { this.p[x] = this.p[this.p[x]]; x = this.p[x]; }
    return x;
  }
  unite(a, b) {
    const ra = this.find(a), rb = this.find(b);
    if (ra === rb) return false;
    if (ra < rb) this.p[rb] = ra; else this.p[ra] = rb;
    return true;
  }
}

function solveMnaCircuit(circuit) {
  const n = circuit.numNodes ?? 1;
  const freqHz = circuit.freqHz ?? 60.0;
  const elements = circuit.elements ?? [];
  const isDC = freqHz <= 1e-6;
  const omega = isDC ? 0.0 : C.kTwoPi * freqHz;

  const condUf = new UnionFind(n);
  const rigidUf = new UnionFind(n);
  const nodeActive = new Uint8Array(n);
  const condDeg = new Int32Array(n);
  const currInj = new Int32Array(n);
  const elemBrRow = new Int32Array(elements.length).fill(-1);
  let numExtra = 0;

  for (let i = 0; i < elements.length; ++i) {
    const e = elements[i];
    const na = e.nodeA, nb = e.nodeB;
    if (na < 0 || na >= n || nb < 0 || nb >= n) {
      return { status: EStatusCode.InvalidInput, offendingElementIndex: i, diagnosticMessage: "Node out of range." };
    }
    switch (e.kind) {
      case EMnaElementKind.Switch:
        if (!e.closed) continue;
        nodeActive[na] = 1; nodeActive[nb] = 1;
        condUf.unite(na, nb); ++condDeg[na]; ++condDeg[nb];
        break;
      case EMnaElementKind.Capacitor:
        nodeActive[na] = 1; nodeActive[nb] = 1;
        if (!isDC) { condUf.unite(na, nb); ++condDeg[na]; ++condDeg[nb]; }
        break;
      case EMnaElementKind.Inductor:
        nodeActive[na] = 1; nodeActive[nb] = 1;
        condUf.unite(na, nb); ++condDeg[na]; ++condDeg[nb];
        if (isDC) {
          if (na !== nb && !rigidUf.unite(na, nb)) return { status: EStatusCode.TopologyError, offendingElementIndex: i, diagnosticMessage: "DC inductor loop." };
          elemBrRow[i] = n + numExtra++;
        }
        break;
      case EMnaElementKind.Resistor:
      case EMnaElementKind.ComplexImpedance:
      case EMnaElementKind.DiodeRectifier:
        nodeActive[na] = 1; nodeActive[nb] = 1;
        condUf.unite(na, nb); ++condDeg[na]; ++condDeg[nb];
        break;
      case EMnaElementKind.VoltageSource:
        nodeActive[na] = 1; nodeActive[nb] = 1;
        condUf.unite(na, nb); ++condDeg[na]; ++condDeg[nb];
        if (na === nb || !rigidUf.unite(na, nb)) return { status: EStatusCode.TopologyError, offendingElementIndex: i, diagnosticMessage: "Voltage source loop." };
        elemBrRow[i] = n + numExtra++;
        break;
      case EMnaElementKind.CurrentSource:
        nodeActive[na] = 1; nodeActive[nb] = 1;
        ++currInj[na]; ++currInj[nb];
        break;
      case EMnaElementKind.Transformer: {
        const nc = e.nodeC, nd = e.nodeD;
        nodeActive[na] = 1; nodeActive[nb] = 1; nodeActive[nc] = 1; nodeActive[nd] = 1;
        condUf.unite(na, nb); condUf.unite(nc, nd);
        ++condDeg[na]; ++condDeg[nb]; ++condDeg[nc]; ++condDeg[nd];
        if (!isDC) elemBrRow[i] = n + numExtra++;
        break;
      }
    }
  }

  for (let i = 0; i < n; ++i) {
    if (currInj[i] > 0 && condDeg[i] === 0) {
      return { status: EStatusCode.TopologyError, offendingElementIndex: -1, diagnosticMessage: "Current source cutset." };
    }
  }

  const rootToIsland = new Int32Array(n).fill(-1);
  const islandRefNodes = [];
  const nodeIslandId = new Int32Array(n).fill(-1);
  if (nodeActive[0]) {
    rootToIsland[condUf.find(0)] = 0;
    islandRefNodes.push(0);
  }
  for (let i = 0; i < n; ++i) {
    if (!nodeActive[i] || condDeg[i] === 0) continue;
    const root = condUf.find(i);
    if (rootToIsland[root] < 0) { rootToIsland[root] = islandRefNodes.length; islandRefNodes.push(i); }
    nodeIslandId[i] = rootToIsland[root];
  }
  let warnings = (islandRefNodes.length > 1 || (islandRefNodes.length === 1 && islandRefNodes[0] !== 0)) ? EPhysicsWarn.WarnFloatingIsland : 0;

  if (islandRefNodes.length > 0) {
    const netRe = new Float64Array(islandRefNodes.length);
    const netIm = new Float64Array(islandRefNodes.length);
    for (let i = 0; i < elements.length; ++i) {
      const e = elements[i];
      if (e.kind !== EMnaElementKind.CurrentSource) continue;
      const iSrc = isDC ? new Complex(e.valueA, 0) : polarComplex(e.valueA, e.valueB ?? 0);
      const ia = nodeIslandId[e.nodeA], ib = nodeIslandId[e.nodeB];
      if (ia >= 0) { netRe[ia] -= iSrc.re; netIm[ia] -= iSrc.im; }
      if (ib >= 0) { netRe[ib] += iSrc.re; netIm[ib] += iSrc.im; }
    }
    for (let isl = 0; isl < islandRefNodes.length; ++isl) {
      if (Math.hypot(netRe[isl], netIm[isl]) > 1e-9) {
        return {
          nodeVoltages: [], nodeIslandId, branchCurrents: [], numIslands: islandRefNodes.length,
          status: EStatusCode.TopologyError, warnings,
          diagnosticMessage: "Galvanic island has unbalanced current source injection (violates KCL cutset).",
        };
      }
    }
  }

  const dim = n + numExtra;
  const A = new Array(dim * dim);
  for (let i = 0; i < dim * dim; ++i) A[i] = new Complex(0, 0);
  const B = new Array(dim);
  for (let i = 0; i < dim; ++i) B[i] = new Complex(0, 0);
  const addY = (r, c, y) => { A[r * dim + c] = A[r * dim + c].add(y); };
  const stampY = (a, b, y) => { if (a === b) return; addY(a, a, y); addY(b, b, y); addY(a, b, y.neg()); addY(b, a, y.neg()); };

  for (let i = 0; i < elements.length; ++i) {
    const e = elements[i];
    const na = e.nodeA, nb = e.nodeB, br = elemBrRow[i];
    switch (e.kind) {
      case EMnaElementKind.Resistor:
        stampY(na, nb, new Complex(1.0 / Math.max(1e-6, e.valueA), 0)); break;
      case EMnaElementKind.Capacitor:
        if (!isDC) stampY(na, nb, new Complex(0, omega * Math.max(1e-15, e.valueA))); break;
      case EMnaElementKind.Inductor:
        if (isDC) { addY(na, br, new Complex(1, 0)); addY(nb, br, new Complex(-1, 0)); addY(br, na, new Complex(1, 0)); addY(br, nb, new Complex(-1, 0)); }
        else stampY(na, nb, new Complex(0, -1.0 / Math.max(1e-6, omega * Math.max(1e-9, e.valueA))));
        break;
      case EMnaElementKind.ComplexImpedance: {
        const z = new Complex(e.valueA, e.valueB ?? 0);
        stampY(na, nb, new Complex(1, 0).div(z.abs() < 1e-6 ? new Complex(1e-6, 0) : z));
        break;
      }
      case EMnaElementKind.DiodeRectifier:
        stampY(na, nb, new Complex(1.0 / (e.closed ? Math.max(1, e.valueA) : 1e6), 0)); break;
      case EMnaElementKind.Switch:
        if (e.closed) stampY(na, nb, new Complex(1.0 / ((e.valueB ?? 0) > 1e-6 ? e.valueB : 1e-3), 0)); break;
      case EMnaElementKind.CurrentSource: {
        const iSrc = isDC ? new Complex(e.valueA, 0) : polarComplex(e.valueA, e.valueB ?? 0);
        B[na] = B[na].sub(iSrc); B[nb] = B[nb].add(iSrc);
        break;
      }
      case EMnaElementKind.VoltageSource: {
        const vSrc = isDC ? new Complex(e.valueA, 0) : polarComplex(e.valueA, e.valueB ?? 0);
        if (br >= 0) {
          addY(na, br, new Complex(-1, 0)); addY(nb, br, new Complex(1, 0));
          addY(br, na, new Complex(1, 0)); addY(br, nb, new Complex(-1, 0));
          B[br] = vSrc;
        }
        break;
      }
      case EMnaElementKind.Transformer:
        if (!isDC && br >= 0) {
          const nr = e.valueA, zl = Math.max(0, e.valueB ?? 0);
          addY(e.nodeC, br, new Complex(-1, 0)); addY(e.nodeD, br, new Complex(1, 0));
          addY(na, br, new Complex(nr, 0)); addY(nb, br, new Complex(-nr, 0));
          addY(br, na, new Complex(nr, 0)); addY(br, nb, new Complex(-nr, 0));
          addY(br, e.nodeC, new Complex(-1, 0)); addY(br, e.nodeD, new Complex(1, 0));
          if (zl > 0) addY(br, br, new Complex(-zl, 0));
        } else {
          stampY(na, nb, new Complex(0.1, 0)); stampY(e.nodeC, e.nodeD, new Complex(0.1, 0));
        }
        break;
    }
  }

  const isRef = new Uint8Array(n);
  for (const r of islandRefNodes) isRef[r] = 1;
  for (let node = 0; node < n; ++node) {
    if (isRef[node] || condDeg[node] === 0) {
      for (let c = 0; c < dim; ++c) A[node * dim + c] = new Complex(0, 0);
      A[node * dim + node] = new Complex(1, 0);
      B[node] = new Complex(0, 0);
    }
  }

  const lin = solveLinearComplexLU(A, B, dim);
  if (lin.status !== EStatusCode.Ok) return { status: lin.status, warnings: warnings | lin.warnings, diagnosticMessage: "Matrix singular." };

  const nodeVoltages = lin.solution.slice(0, n);
  const branchCurrents = elements.map((e, idx) => {
    const vd = nodeVoltages[e.nodeA].sub(nodeVoltages[e.nodeB]);
    const br = elemBrRow[idx];
    switch (e.kind) {
      case EMnaElementKind.Resistor: return vd.scale(1.0 / Math.max(1e-6, e.valueA));
      case EMnaElementKind.Capacitor: return isDC ? new Complex(0, 0) : vd.mul(new Complex(0, omega * Math.max(1e-15, e.valueA)));
      case EMnaElementKind.Inductor: return isDC ? (br >= 0 ? lin.solution[br] : new Complex(0, 0)) : vd.mul(new Complex(0, -1.0 / Math.max(1e-6, omega * Math.max(1e-9, e.valueA))));
      case EMnaElementKind.ComplexImpedance: { const z = new Complex(e.valueA, e.valueB ?? 0); return vd.div(z.abs() < 1e-6 ? new Complex(1e-6, 0) : z); }
      case EMnaElementKind.Switch: return e.closed ? vd.scale(1.0 / ((e.valueB ?? 0) > 1e-6 ? e.valueB : 1e-3)) : new Complex(0, 0);
      case EMnaElementKind.CurrentSource: return isDC ? new Complex(e.valueA, 0) : polarComplex(e.valueA, e.valueB ?? 0);
      case EMnaElementKind.VoltageSource:
      case EMnaElementKind.Transformer: return br >= 0 ? lin.solution[br] : new Complex(0, 0);
      case EMnaElementKind.DiodeRectifier: return vd.scale(1.0 / (e.closed ? Math.max(1, e.valueA) : 1e6));
      default: return new Complex(0, 0);
    }
  });

  const sol = {
    nodeVoltages, nodeIslandId, branchCurrents, numIslands: islandRefNodes.length,
    scaledResidual: lin.scaledResidual, minPivotRatio: lin.minPivotRatio,
    status: EStatusCode.Ok, warnings: warnings | lin.warnings,
    readVoltmeter(nodePlus, nodeMinus, loZ = false) {
      if (nodePlus < 0 || nodePlus >= n || nodeMinus < 0 || nodeMinus >= n) return { magnitude: 0, angleDeg: 0, floating: true, status: EStatusCode.InvalidInput };
      if (loZ && nodePlus !== nodeMinus) {
        const loaded = solveMnaCircuit({
          numNodes: n,
          freqHz,
          elements: [
            ...elements,
            { kind: EMnaElementKind.Resistor, name: "__LoZProbe3k", nodeA: nodePlus, nodeB: nodeMinus, valueA: 3000.0, valueB: 0.0, closed: true },
          ],
        });
        if (loaded.status === EStatusCode.Ok || loaded.status === EStatusCode.FloatingIsland) {
          return loaded.readVoltmeter(nodePlus, nodeMinus, false);
        }
        return { magnitude: 0, angleDeg: 0, floating: true, status: loaded.status };
      }
      const ia = nodeIslandId[nodePlus], ib = nodeIslandId[nodeMinus];
      if (ia < 0 || ib < 0 || ia !== ib) return { magnitude: 0, angleDeg: 0, floating: true, status: EStatusCode.FloatingIsland };
      const vd = nodeVoltages[nodePlus].sub(nodeVoltages[nodeMinus]);
      return { magnitude: vd.abs(), angleDeg: vd.argDeg(), floating: false, status: EStatusCode.Ok };
    },
    readAmmeter(idx) {
      if (idx < 0 || idx >= branchCurrents.length) return { magnitude: 0, angleDeg: 0, status: EStatusCode.InvalidInput };
      return { magnitude: branchCurrents[idx].abs(), angleDeg: branchCurrents[idx].argDeg(), status: EStatusCode.Ok };
    },
  };
  return sol;
}

function measureDeenergizedOhms(circuit, nodeA, nodeB) {
  if (nodeA === nodeB) return { magnitude: 0, openCircuit: false, status: EStatusCode.Ok };
  const testElements = (circuit.elements ?? []).filter((e) => e.kind !== EMnaElementKind.VoltageSource && e.kind !== EMnaElementKind.CurrentSource);
  testElements.push({ kind: EMnaElementKind.CurrentSource, nodeA: nodeB, nodeB: nodeA, valueA: 1.0, valueB: 0.0, closed: true });
  const sol = solveMnaCircuit({ numNodes: circuit.numNodes, freqHz: 0.0, elements: testElements });
  if (sol.status !== EStatusCode.Ok || sol.nodeIslandId[nodeA] < 0 || sol.nodeIslandId[nodeA] !== sol.nodeIslandId[nodeB]) {
    return { magnitude: 1e12, openCircuit: true, status: EStatusCode.FloatingIsland };
  }
  return { magnitude: sol.readVoltmeter(nodeA, nodeB).magnitude, openCircuit: false, status: EStatusCode.Ok };
}

  return { solveMnaCircuit, measureDeenergizedOhms, EMnaElementKind };
  })();

  _M.Controls = (function() {
const { EStatusCode, clampFinite, lerpVal, safeDiv } = _M.Types;
const U = _M.Units;

const EFurnaceSeqState = Object.freeze({
  Idle: 0, InducerPurge: 1, PressureSwitchProve: 2, IgniterWarmup: 3,
  TrialForIgnition: 4, FlameProve: 5, BlowerDelay: 6, HeatingRun: 7,
  PostPurge: 8, SoftLockout: 9, LimitSwitchTrip: 10,
});

const EFaultHypothesisId = Object.freeze({
  Normal: 0, Undercharge: 1, Overcharge: 2, LowEvapAirflow: 3, DirtyCondenser: 4,
  LiquidLineRestriction: 5, NonCondensables: 6, InefficientCompressor: 7, OverfeedingTxv: 8,
});

function stepPid(state, config, setpoint, measured, dtSec) {
  const outMin = config.outMin ?? 0.0, outMax = config.outMax ?? 100.0;
  if (!Number.isFinite(dtSec) || dtSec <= 0.0) {
    if (!state.initialized) {
      state.prevMeasured = measured;
      state.derivFiltered = 0.0;
      state.lastOutput = clampFinite(state.lastOutput ?? 0.0, outMin, outMax);
      state.initialized = true;
    }
    return state.lastOutput;
  }
  const dt = dtSec;
  const sign = config.reverseActing ? -1.0 : 1.0;
  const err = sign * (setpoint - measured);
  if (!state.initialized) { state.prevMeasured = measured; state.derivFiltered = 0.0; state.initialized = true; }
  const rawDeriv = -sign * ((measured - state.prevMeasured) / dt);
  const alpha = dt / (Math.max(1e-4, config.derivFilterTauSec ?? 1.0) + dt);
  state.derivFiltered += alpha * (rawDeriv - state.derivFiltered);
  state.prevMeasured = measured;
  const p = config.kp * err, d = (config.kd ?? 0.0) * state.derivFiltered;
  const candI = state.integral + (config.ki ?? 0.0) * err * dt;
  const maxDelta = Math.max(0.0, config.slewRatePerSec ?? 1000.0) * dt;
  const effMin = maxDelta > 0.0 ? Math.max(outMin, state.lastOutput - maxDelta) : outMin;
  const effMax = maxDelta > 0.0 ? Math.min(outMax, state.lastOutput + maxDelta) : outMax;
  let unclamped = p + candI + d;
  if (unclamped > effMax) { if ((config.ki ?? 0) * err < 0) state.integral = candI; unclamped = effMax; }
  else if (unclamped < effMin) { if ((config.ki ?? 0) * err > 0) state.integral = candI; unclamped = effMin; }
  else { state.integral = candI; }
  const finalOut = clampFinite(unclamped, outMin, outMax);
  state.lastOutput = finalOut;
  return finalOut;
}

function stepHysteresisSwitch(prevOn, value, setpoint, differential, turnOnAbove = true) {
  const half = Math.max(0.0, differential) * 0.5;
  if (turnOnAbove) { if (value >= setpoint + half) return true; if (value <= setpoint - half) return false; return prevOn; }
  if (value <= setpoint - half) return true;
  if (value >= setpoint + half) return false;
  return prevOn;
}

function stepFurnaceSequence(ctx, inputs, dtSec) {
  const dt = Math.max(0.0, dtSec);
  if (inputs.resetPower) {
    ctx.state = EFurnaceSeqState.Idle;
    ctx.stateTimerSec = 0.0;
    ctx.retryCount = 0;
    ctx.inducerOn = false;
    ctx.igniterOn = false;
    ctx.gasValveOpen = false;
    ctx.blowerOn = false;
    ctx.rolloutLatched = false;
    return ctx.state;
  }
  if (!inputs.rolloutClosed || ctx.rolloutLatched) {
    ctx.rolloutLatched = true;
    ctx.state = EFurnaceSeqState.LimitSwitchTrip;
    ctx.gasValveOpen = false;
    ctx.igniterOn = false;
    ctx.blowerOn = true;
    ctx.inducerOn = true;
    ctx.stateTimerSec = 0.0;
    return ctx.state;
  }
  if (!inputs.highLimitClosed) {
    ctx.state = EFurnaceSeqState.LimitSwitchTrip;
    ctx.gasValveOpen = false;
    ctx.igniterOn = false;
    ctx.blowerOn = true;
    ctx.inducerOn = true;
    ctx.stateTimerSec = 0.0;
    return ctx.state;
  }
  if (ctx.state === EFurnaceSeqState.SoftLockout) {
    ctx.stateTimerSec = (ctx.stateTimerSec ?? 0.0) + dt;
    ctx.gasValveOpen = false;
    ctx.igniterOn = false;
    ctx.inducerOn = false;
    if (ctx.stateTimerSec >= 90.0) ctx.blowerOn = false;
    if (ctx.stateTimerSec >= 3600.0) {
      ctx.retryCount = 0;
      ctx.state = EFurnaceSeqState.Idle;
      ctx.stateTimerSec = 0.0;
    }
    return ctx.state;
  }

  ctx.stateTimerSec = (ctx.stateTimerSec ?? 0.0) + dt;
  if (!inputs.callW1 && ctx.state !== EFurnaceSeqState.Idle && ctx.state !== EFurnaceSeqState.PostPurge && ctx.state !== EFurnaceSeqState.LimitSwitchTrip) {
    ctx.state = EFurnaceSeqState.PostPurge;
    ctx.stateTimerSec = 0.0;
  }

  switch (ctx.state) {
    case EFurnaceSeqState.Idle:
      ctx.inducerOn = false; ctx.igniterOn = false; ctx.gasValveOpen = false; ctx.blowerOn = false;
      if (inputs.callW1) {
        if (inputs.pressureSwitchClosed) {
          if (ctx.stateTimerSec >= 30.0) { ctx.state = EFurnaceSeqState.SoftLockout; ctx.stateTimerSec = 0.0; }
        } else {
          ctx.state = EFurnaceSeqState.InducerPurge; ctx.stateTimerSec = 0.0;
        }
      } else {
        ctx.stateTimerSec = 0.0;
      }
      break;
    case EFurnaceSeqState.InducerPurge:
      ctx.inducerOn = true;
      if (ctx.stateTimerSec >= 10.0) { ctx.state = EFurnaceSeqState.PressureSwitchProve; ctx.stateTimerSec = 0.0; }
      break;
    case EFurnaceSeqState.PressureSwitchProve:
      ctx.inducerOn = true;
      if (inputs.pressureSwitchClosed) {
        ctx.state = EFurnaceSeqState.IgniterWarmup; ctx.stateTimerSec = 0.0;
      } else if (ctx.stateTimerSec >= 30.0) {
        ctx.retryCount = (ctx.retryCount ?? 0) + 1;
        ctx.state = ctx.retryCount >= 3 ? EFurnaceSeqState.SoftLockout : EFurnaceSeqState.InducerPurge;
        ctx.stateTimerSec = 0.0;
      }
      break;
    case EFurnaceSeqState.IgniterWarmup:
      ctx.inducerOn = true;
      if (!inputs.pressureSwitchClosed) {
        ctx.igniterOn = false;
        ctx.retryCount = (ctx.retryCount ?? 0) + 1;
        ctx.state = ctx.retryCount >= 3 ? EFurnaceSeqState.SoftLockout : EFurnaceSeqState.InducerPurge;
        ctx.stateTimerSec = 0.0;
        break;
      }
      ctx.igniterOn = true;
      if (ctx.stateTimerSec >= 17.0) { ctx.state = EFurnaceSeqState.TrialForIgnition; ctx.stateTimerSec = 0.0; }
      break;
    case EFurnaceSeqState.TrialForIgnition:
      ctx.inducerOn = true;
      if (!inputs.pressureSwitchClosed) {
        ctx.gasValveOpen = false; ctx.igniterOn = false;
        ctx.retryCount = (ctx.retryCount ?? 0) + 1;
        ctx.state = ctx.retryCount >= 3 ? EFurnaceSeqState.SoftLockout : EFurnaceSeqState.InducerPurge;
        ctx.stateTimerSec = 0.0;
        break;
      }
      ctx.igniterOn = true; ctx.gasValveOpen = true;
      if ((inputs.flameMicroAmps ?? 0.0) >= 1.5 && ctx.stateTimerSec >= 1.0) {
        ctx.state = EFurnaceSeqState.FlameProve; ctx.stateTimerSec = 0.0;
      } else if (ctx.stateTimerSec >= 4.0) {
        ctx.gasValveOpen = false; ctx.igniterOn = false;
        ctx.retryCount = (ctx.retryCount ?? 0) + 1;
        ctx.state = ctx.retryCount >= 3 ? EFurnaceSeqState.SoftLockout : EFurnaceSeqState.InducerPurge;
        ctx.stateTimerSec = 0.0;
      }
      break;
    case EFurnaceSeqState.FlameProve:
      ctx.igniterOn = false;
      if (!inputs.pressureSwitchClosed) {
        ctx.gasValveOpen = false;
        ctx.retryCount = (ctx.retryCount ?? 0) + 1;
        ctx.state = ctx.retryCount >= 3 ? EFurnaceSeqState.SoftLockout : EFurnaceSeqState.InducerPurge;
        ctx.stateTimerSec = 0.0;
        break;
      }
      ctx.gasValveOpen = true;
      ctx.state = EFurnaceSeqState.BlowerDelay; ctx.stateTimerSec = 0.0;
      break;
    case EFurnaceSeqState.BlowerDelay:
      if (!inputs.pressureSwitchClosed || (inputs.flameMicroAmps ?? 0.0) < 0.8) {
        ctx.gasValveOpen = false;
        ctx.retryCount = (ctx.retryCount ?? 0) + 1;
        ctx.state = ctx.retryCount >= 3 ? EFurnaceSeqState.SoftLockout : EFurnaceSeqState.InducerPurge;
        ctx.stateTimerSec = 0.0;
        break;
      }
      ctx.gasValveOpen = true;
      if (ctx.stateTimerSec >= 30.0) {
        ctx.state = EFurnaceSeqState.HeatingRun;
        ctx.blowerOn = true;
        ctx.stateTimerSec = 0.0;
      }
      break;
    case EFurnaceSeqState.HeatingRun:
      ctx.inducerOn = true; ctx.blowerOn = true;
      if (!inputs.pressureSwitchClosed || (inputs.flameMicroAmps ?? 0.0) < 0.8) {
        ctx.gasValveOpen = false;
        ctx.retryCount = (ctx.retryCount ?? 0) + 1;
        ctx.state = ctx.retryCount >= 3 ? EFurnaceSeqState.SoftLockout : EFurnaceSeqState.InducerPurge;
        ctx.stateTimerSec = 0.0;
        break;
      }
      ctx.gasValveOpen = true;
      if (ctx.stateTimerSec >= 30.0) ctx.retryCount = 0;
      break;
    case EFurnaceSeqState.LimitSwitchTrip:
      ctx.gasValveOpen = false; ctx.igniterOn = false;
      ctx.state = EFurnaceSeqState.PostPurge;
      ctx.stateTimerSec = 0.0;
      break;
    case EFurnaceSeqState.PostPurge:
      ctx.gasValveOpen = false; ctx.igniterOn = false;
      ctx.inducerOn = ctx.stateTimerSec < 15.0;
      ctx.blowerOn = ctx.stateTimerSec < 90.0;
      if (ctx.stateTimerSec >= 90.0) { ctx.retryCount = 0; ctx.state = EFurnaceSeqState.Idle; ctx.stateTimerSec = 0.0; }
      break;
    default:
      break;
  }
  return ctx.state;
}

function ntc10kResistanceFromTempF(tempF, typeIII = false) {
  const tk = clampFinite(U.fToK(tempF), 180.0, 460.0);
  return 10000.0 * Math.exp((typeIII ? 3694.0 : 3892.0) * (1.0 / tk - 1.0 / 298.15));
}

function ntc10kTempFFromResistance(ohms, typeIII = false) {
  const r = clampFinite(ohms, 10.0, 5.0e6);
  const invT = (1.0 / 298.15) + (1.0 / (typeIII ? 3694.0 : 3892.0)) * Math.log(r / 10000.0);
  return U.kToF(1.0 / invT);
}

function rtdResistanceFromTempF(tempF, r0 = 1000.0) {
  const tc = U.fToC(tempF);
  let poly = 1.0 + 3.9083e-3 * tc - 5.775e-7 * tc * tc;
  if (tc < 0.0) poly += -4.183e-12 * (tc - 100.0) * tc * tc * tc;
  return r0 * poly;
}

function rtdTempFFromResistance(ohms, r0 = 1000.0) {
  const A = 3.9083e-3, B = -5.775e-7, C = -4.183e-12;
  const ratio = Math.max(0.1, ohms) / Math.max(1.0, r0);
  const disc = A * A - 4.0 * B * (1.0 - ratio);
  let tc = (-A + Math.sqrt(Math.max(0.0, disc))) / (2.0 * B);
  if (ratio < 1.0) {
    for (let i = 0; i < 5; ++i) {
      const f = 1.0 + A * tc + B * tc * tc + C * (tc - 100.0) * tc * tc * tc - ratio;
      const df = A + 2.0 * B * tc + C * (4.0 * tc * tc * tc - 300.0 * tc * tc);
      tc -= f / df;
    }
  }
  return U.cToF(tc);
}

function scale4To20Ma(ma, engMin, engMax) {
  if (!Number.isFinite(ma) || ma < 3.5 || ma > 21.0) {
    return { status: EStatusCode.OutOfRange, value: lerpVal(engMin, engMax, (clampFinite(ma, 4.0, 20.0) - 4.0) / 16.0) };
  }
  return { status: (ma < 4.0 || ma > 20.0) ? EStatusCode.Clamped : EStatusCode.Ok, value: lerpVal(engMin, engMax, clampFinite((ma - 4.0) / 16.0, 0.0, 1.0)) };
}

const scale0To10V = (volts, engMin, engMax) => lerpVal(engMin, engMax, clampFinite(volts / 10.0, 0.0, 1.0));
const stepFirstOrderLag = (prev, target, tauSec, dtSec) => prev + (1.0 - Math.exp(-Math.max(0.0, dtSec) / Math.max(1e-4, tauSec))) * (target - prev);
const calcControlAuthority = (valveDropPsi, sysDropPsi) => safeDiv(Math.max(0, valveDropPsi), Math.max(0, valveDropPsi) + Math.max(0, sysDropPsi), 0.0);

function evalInstalledValveFlowFrac(stemPos01, authorityN, equalPct = true, rangeability = 50.0) {
  const s = clampFinite(stemPos01, 0.0, 1.0), n = clampFinite(authorityN, 0.01, 1.0);
  const intr = equalPct ? (s <= 1e-4 ? 0.0 : Math.pow(Math.max(2.0, rangeability), s - 1.0)) : s;
  return intr / Math.sqrt(n + (1.0 - n) * intr * intr);
}

function diagnoseSystemFaults(obs) {
  const shErr = obs.superheatF - obs.targetSuperheatF, scErr = obs.subcoolingF - obs.targetSubcoolingF;
  const suct = obs.suctionSatDeltaF, head = obs.dischargeSatDeltaF;
  const isTxv = obs.isTxv !== undefined ? !!obs.isTxv : true;
  const g = (v, c, s) => Math.exp(-0.5 * ((v - c) / s) ** 2);
  const list = [
    { fault: EFaultHypothesisId.Normal, name: "Normal Operation", confidenceScore: 0.25 * (g(suct, 0, 4) + g(head, 0, 5) + g(shErr, 0, 3) + g(scErr, 0, 3)), verificationHint: "Check superheat, subcooling, and supply delta-T against design." },
    { fault: EFaultHypothesisId.Undercharge, name: "Low Refrigerant Charge (Leak)", confidenceScore: 0.30 * g(suct, -12, 7) + 0.25 * g(head, -8, 7) + 0.25 * g(shErr, 15, 8) + 0.20 * g(scErr, -8, 4), verificationHint: "Verify flash-gas in sight glass and perform electronic/bubble leak test." },
    { fault: EFaultHypothesisId.Overcharge, name: "Overcharged System", confidenceScore: 0.35 * g(head, 16, 8) + 0.35 * g(scErr, 12, 6) + 0.30 * g(obs.ampDrawRatio, 1.18, 0.12), verificationHint: "Verify high subcooling and elevated head pressure; recover excess refrigerant." },
    { fault: EFaultHypothesisId.LowEvapAirflow, name: "Low Evaporator Airflow / Dirty Filter", confidenceScore: 0.35 * g(suct, -10, 6) + 0.30 * g(obs.evapAirDeltaTF, 26, 4) + 0.35 * g(shErr, -6, 5), verificationHint: "Inspect air filter, blower wheel, static pressure (TESP), and evaporator fins." },
    { fault: EFaultHypothesisId.DirtyCondenser, name: "Dirty Condenser Coil / Weak Condenser Fan", confidenceScore: 0.40 * g(head, 22, 9) + 0.30 * g(suct, 5, 5) + 0.30 * g(obs.ampDrawRatio, 1.25, 0.15), verificationHint: "Inspect outdoor coil matting, condenser fan motor amp draw, and capacitor uF." },
    { fault: EFaultHypothesisId.LiquidLineRestriction, name: "Liquid Line Restriction (Clogged Filter-Drier)", confidenceScore: 0.35 * g(suct, -12, 7) + 0.35 * g(shErr, 16, 8) + 0.30 * g(scErr, 8, 6), verificationHint: "Measure temperature drop (> 2 F) across liquid-line filter-drier." },
    { fault: EFaultHypothesisId.NonCondensables, name: "Non-Condensables (Air/N2 in System)", confidenceScore: 0.50 * g(head, 20, 9) + 0.30 * g(scErr, 6, 6) + 0.20 * g(obs.ampDrawRatio, 1.15, 0.12), verificationHint: "Perform off-cycle standing P/T check after ambient stabilization." },
    { fault: EFaultHypothesisId.InefficientCompressor, name: "Inefficient Compressor (Bad Valves / Scroll Bypass)", confidenceScore: 0.40 * g(suct, 12, 6) + 0.35 * g(head, -10, 6) + 0.25 * g(obs.ampDrawRatio, 0.72, 0.15), verificationHint: "Check compression ratio and pump-down / suction-hold capability." },
    { fault: EFaultHypothesisId.OverfeedingTxv, name: "Overfeeding TXV / Unstrapped Sensing Bulb", confidenceScore: (isTxv ? 1.0 : 0.05) * (0.45 * g(shErr, -8, 3) + 0.30 * g(suct, 6, 5) + 0.25 * g(scErr, -4, 4)), verificationHint: "Verify TXV sensing bulb strap tightness, insulation, and superheat spring setting." },
  ];
  list.sort((a, b) => b.confidenceScore - a.confidenceScore);
  return list;
}

function stepTrimAndRespond(currentSetpoint, requestsR, config = {}) {
  const ignore = Math.max(0, Math.trunc(config.ignoreRequests ?? 2));
  const netReq = Math.max(0, Math.trunc(requestsR) - ignore);
  const trim = config.trimAmount ?? -0.04;
  const resp = config.respondAmount ?? 0.06;
  const maxStep = Math.abs(config.maxRespondStep ?? 0.15);
  const delta = netReq === 0 ? trim : clampFinite(netReq * resp, -maxStep, maxStep);
  const minSp = config.minSetpoint ?? 0.5, maxSp = config.maxSetpoint ?? 2.5;
  return clampFinite(currentSetpoint + delta, Math.min(minSp, maxSp), Math.max(minSp, maxSp));
}

function calcAshrae621Ventilation(rpCfmPerPerson, people, raCfmPerFt2, areaFt2, ez = 1.0) {
  const vbz = Math.max(0.0, rpCfmPerPerson) * Math.max(0.0, people) + Math.max(0.0, raCfmPerFt2) * Math.max(0.0, areaFt2);
  const ezSafe = clampFinite(ez, 0.2, 1.5);
  return { breathingZoneCfmVbz: vbz, zoneOutdoorCfmVoz: vbz / ezSafe };
}

  return { stepPid, stepHysteresisSwitch, stepFurnaceSequence, ntc10kResistanceFromTempF, ntc10kTempFFromResistance, rtdResistanceFromTempF, rtdTempFFromResistance, scale4To20Ma, evalInstalledValveFlowFrac, diagnoseSystemFaults, stepTrimAndRespond, calcAshrae621Ventilation, EFurnaceSeqState, EFaultHypothesisId, scale0To10V, stepFirstOrderLag, calcControlAuthority };
  })();

  _M.AdvancedElectrical = (function() {
const C = _M.Constants;
const { Complex, EStatusCode, clampFinite, safeDiv } = _M.Types;

function solveSteinmetzInductionMotor(input = {}) {
  const vll = input.lineToLineV ?? 460.0;
  const freqIn = input.freqHz ?? 60.0;
  const polesIn = input.poles ?? 4;
  const r1In = input.r1Ohms ?? 0.65;
  const x1In = input.x1Ohms ?? 1.40;
  const r2In = input.r2Ohms ?? 0.45;
  const x2In = input.x2Ohms ?? 1.35;
  const xmIn = input.xmOhms ?? 32.0;
  const rcIn = input.rcOhms ?? 400.0;
  const slipIn = input.slip ?? 0.035;
  const fwIn = input.frictionWindageW ?? 120.0;

  if (!Number.isFinite(vll) || vll <= 1.0
    || !Number.isFinite(freqIn) || !Number.isFinite(polesIn)
    || !Number.isFinite(r1In) || !Number.isFinite(x1In)
    || !Number.isFinite(r2In) || !Number.isFinite(x2In)
    || !Number.isFinite(xmIn) || !Number.isFinite(rcIn)
    || !Number.isFinite(slipIn) || !Number.isFinite(fwIn)) {
    return {
      syncRpm: 0.0,
      shaftRpm: 0.0,
      slip: 0.0,
      statorCurrentA: 0.0,
      rotorCurrentA: 0.0,
      lockedRotorCurrentA: 0.0,
      inputPowerW: 0.0,
      airGapPowerW: 0.0,
      shaftPowerHp: 0.0,
      shaftTorqueFtLb: 0.0,
      breakdownSlip: 0.0,
      breakdownTorqueFtLb: 0.0,
      powerFactor: 0.0,
      efficiency: 0.0,
      status: EStatusCode.InvalidInput,
    };
  }

  const freq = Math.max(1.0, freqIn);
  const poles = Math.max(2, Math.trunc(polesIn));
  const syncRpm = (120.0 * freq) / poles;
  const omegaSync = C.kTwoPi * syncRpm / 60.0;
  const slipClamped = slipIn < 1e-6 || slipIn > 1.0;
  const slip = clampFinite(slipIn, 1e-6, 1.0);
  const shaftRpm = syncRpm * (1.0 - slip);

  const r1 = Math.max(1e-5, r1In);
  const x1 = Math.max(0.0, x1In);
  const r2 = Math.max(1e-5, r2In);
  const x2 = Math.max(0.0, x2In);
  const xm = Math.max(0.1, xmIn);
  const rc = Math.max(1.0, rcIn);
  const fw = Math.max(0.0, fwIn);

  const Z1 = new Complex(r1, x1);
  const Ym = new Complex(1.0 / rc, -1.0 / xm);
  const Zm = new Complex(1.0, 0.0).div(Ym);

  const V1 = new Complex(vll / C.kSqrt3, 0.0);
  const ZRot = new Complex(r2 / slip, x2);
  const ZPar = Zm.mul(ZRot).div(Zm.add(ZRot));
  const ZTotal = Z1.add(ZPar);
  const I1 = V1.div(ZTotal);
  const E1 = V1.sub(I1.mul(Z1));
  const I2 = E1.div(ZRot);

  const ZTh = Z1.mul(Zm).div(Z1.add(Zm));
  const VTh = V1.mul(Zm.div(Z1.add(Zm)));
  const vThMag = VTh.abs();
  const rTh = ZTh.re;
  const xTh = ZTh.im;

  const zB = Math.sqrt(rTh * rTh + (xTh + x2) * (xTh + x2));
  const sMax = r2 / Math.max(1e-6, zB);
  const pAgMax = 3.0 * vThMag * vThMag / Math.max(1e-6, 2.0 * (rTh + zB));
  const tMaxNm = pAgMax / Math.max(1e-6, omegaSync);

  const zLraRot = new Complex(r2, x2);
  const I_Lra = V1.div(Z1.add(Zm.mul(zLraRot).div(Zm.add(zLraRot))));

  const i1Mag = I1.abs();
  const i2Mag = I2.abs();
  const SIn = V1.mul(I1.conj()).scale(3.0);
  const pIn = Math.max(0.0, SIn.re);
  const pAg = 3.0 * i2Mag * i2Mag * (r2 / slip);
  const tEmNm = pAg / Math.max(1e-6, omegaSync);
  const tFwNm = fw / Math.max(1e-6, omegaSync);
  const pMechGrossW = pAg * (1.0 - slip);
  const pShaftW = Math.max(0.0, pMechGrossW - fw);
  const shaftTorqueNm = (slip < 1.0 - 1e-6)
    ? (pShaftW / (Math.max(1e-6, omegaSync) * (1.0 - slip)))
    : Math.max(0.0, tEmNm - tFwNm);
  const kNmToFtLb = 0.737562149277;

  return {
    syncRpm,
    shaftRpm,
    slip,
    statorCurrentA: i1Mag,
    rotorCurrentA: i2Mag,
    lockedRotorCurrentA: I_Lra.abs(),
    inputPowerW: pIn,
    airGapPowerW: pAg,
    shaftPowerHp: pShaftW / C.kWattsPerHp,
    shaftTorqueFtLb: shaftTorqueNm * kNmToFtLb,
    breakdownSlip: sMax,
    breakdownTorqueFtLb: tMaxNm * kNmToFtLb,
    powerFactor: clampFinite(safeDiv(pIn, C.kSqrt3 * Math.max(1e-6, vll * i1Mag), 0.0), 0.0, 1.0),
    efficiency: clampFinite(safeDiv(pShaftW, pIn, 0.0), 0.0, 1.0),
    status: slipClamped ? EStatusCode.Clamped : EStatusCode.Ok,
  };
}

function calcSymmetricalComponents(va, vb, vc) {
  const alpha = new Complex(-0.5, C.kSqrt3 * 0.5);
  const alpha2 = new Complex(-0.5, -C.kSqrt3 * 0.5);
  const third = 1.0 / 3.0;

  const zeroSeqV = va.add(vb).add(vc).scale(third);
  const posSeqV = va.add(alpha.mul(vb)).add(alpha2.mul(vc)).scale(third);
  const negSeqV = va.add(alpha2.mul(vb)).add(alpha.mul(vc)).scale(third);

  const zeroSeqMagV = zeroSeqV.abs();
  const posSeqMagV = posSeqV.abs();
  const negSeqMagV = negSeqV.abs();

  let negSequenceUnbalancePct = 0.0;
  let zeroSequenceUnbalancePct = 0.0;
  if (posSeqMagV > 1e-6) {
    negSequenceUnbalancePct = (negSeqMagV / posSeqMagV) * 100.0;
    zeroSequenceUnbalancePct = (zeroSeqMagV / posSeqMagV) * 100.0;
  } else if (negSeqMagV > 1e-6 || zeroSeqMagV > 1e-6) {
    negSequenceUnbalancePct = negSeqMagV > 1e-6 ? 100.0 : 0.0;
    zeroSequenceUnbalancePct = zeroSeqMagV > 1e-6 ? 100.0 : 0.0;
  }

  let motorDeratingFactor = 1.0;
  if (posSeqMagV <= 1e-6 && (negSeqMagV > 1e-6 || zeroSeqMagV > 1e-6)) {
    motorDeratingFactor = 0.50;
  } else {
    const u = negSequenceUnbalancePct;
    motorDeratingFactor = u <= 1.0
      ? 1.0
      : clampFinite(1.0 - 0.055 * (u - 1.0) - 0.002 * (u - 1.0) * (u - 1.0), 0.50, 1.0);
  }

  return {
    zeroSeqV, posSeqV, negSeqV,
    zeroSeqMagV, posSeqMagV, negSeqMagV,
    negSequenceUnbalancePct, zeroSequenceUnbalancePct, motorDeratingFactor,
  };
}

  return { solveSteinmetzInductionMotor, calcSymmetricalComponents };
  })();

  return _M;
});