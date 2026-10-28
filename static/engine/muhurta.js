// Muhurta analysis offline: line-by-line port of the server's
// services/muhurta_analysis.py (analyze_all_grahas, screen_muhurta).
// The Python file is the authority — the July 2026 consolidation fixed
// seven JS/Python drifts there — so keep this a faithful copy: same
// conditions, same order of floating-point operations, same output fields
// (None → null). tests/engine-muhurta-parity.spec.js checks it against
// POST /api/v1/muhurta/screen.

// ─── Jyotish constants ─────────────────────────────────────────────────────

const DEBI_RASHI = { Sun: 7, Moon: 8, Mars: 4, Mercury: 12, Jupiter: 10, Venus: 6, Saturn: 1, Rahu: 8, Ketu: 2 };
const EXALT_RASHI = { Sun: 1, Moon: 2, Mars: 10, Mercury: 6, Jupiter: 4, Venus: 12, Saturn: 7, Rahu: 2, Ketu: 8 };
const MOOLA_RASHI = { Sun: 5, Moon: 4, Mars: 1, Mercury: 6, Jupiter: 9, Venus: 7, Saturn: 11 };
const MOOLA_LORD = { 1: 'Mars', 4: 'Moon', 5: 'Sun', 6: 'Mercury', 7: 'Venus', 9: 'Jupiter', 11: 'Saturn' };
export const RASHI_NAME = ['', 'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
  'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

const FUNC_MALEFICS = {
  1: ['Mercury'], 2: ['Mars', 'Venus', 'Jupiter'], 3: [], 4: ['Jupiter', 'Saturn'], 5: ['Moon'],
  6: ['Sun', 'Saturn', 'Mars'], 7: ['Mercury'], 8: ['Venus', 'Mars'], 9: ['Moon'], 10: ['Sun', 'Jupiter'],
  11: ['Moon', 'Mercury'], 12: ['Sun', 'Venus', 'Saturn'],
};
const MMP = { 1: 'Ketu', 2: 'Jupiter', 3: 'Ketu', 4: 'Saturn', 5: 'Moon', 6: 'Mars',
  7: 'Mercury', 8: 'Venus', 9: 'Moon', 10: 'Sun', 11: 'Mercury', 12: 'Venus' };

const COMBUST_ORB = { Moon: 12, Mars: 17, Mercury: 14, Jupiter: 11, Venus: 10, Saturn: 16 };
const ASPECT_OFFSETS = { default: [6], Mars: [6, 3, 7], Jupiter: [6, 4, 8],
  Saturn: [6, 2, 9], Rahu: [6, 4, 8], Ketu: [6, 4, 8] };
const DUSHTANA = new Set([6, 8, 12]);

const MUHURTA_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
const LAGNA_RULER = { 1: 'Mars', 2: 'Moon', 3: 'Sun', 4: 'Moon', 5: 'Sun', 6: 'Mercury',
  7: 'Venus', 8: 'Jupiter', 9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Mars' };
const NAK_LORDS_27 = Array.from({ length: 27 }, (_, i) =>
  ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'][i % 9]);

// Canonical "Ideal" screening config (= IDEAL_CFG / GET /muhurta/ideal-cfg).
export const IDEAL_CFG = {
  minBeneficDays: 30, antarMin: 0.70, lagnaLordMin: 0.70,
  minStrongPlanets: 4, minStrongHouses: 7, mepOrb: 5,
  planetMins: {}, allowWeakAntar: false, lowerStrongThreshold: false,
  noFmLagna: true,
};

// ─── Python semantics helpers ──────────────────────────────────────────────

const isNodeName = n => n === 'Rahu' || n === 'Ketu';
const get = (o, k, d) => (o && k in o ? o[k] : d);           // dict.get(k, d)
const truthy = v => !(v === undefined || v === null || v === false || v === 0 || v === '');
// round() is round-half-to-even in Python
function pyRound(x) {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
}
// f'{x:.1f}': like toFixed(1), but an exact tie (e.g. 0.25) rounds to even
function fmt1(x) {
  const t = x * 10;
  if (Math.abs(t % 1) === 0.5 && Number.isInteger(t * 2)) {
    const r = pyRound(t);
    return (r / 10).toFixed(1);
  }
  return x.toFixed(1);
}
const isPlanet = a => a !== null && typeof a === 'object' && 'graha' in a;
// ISO datetime → integer microseconds (datetime.fromisoformat precision)
function isoUs(iso) {
  const [main, frac = ''] = iso.split('.');
  return Date.parse(main + 'Z') * 1000 + Number((frac + '000000').slice(0, 6));
}

// ─── Helpers ───────────────────────────────────────────────────────────────

// Python returns a set; callers only test membership or iterate it, and
// iteration order only matters for exact ties in mep_orb_detail.
export function fmAspectedHouses(graha, fromHouse) {
  const houses = new Set([fromHouse]);
  for (const off of ASPECT_OFFSETS[graha] || ASPECT_OFFSETS.default) houses.add(((fromHouse - 1 + off) % 12) + 1);
  return houses;
}

export function absDiffDeg(rashiA, degA, rashiB, degB) {
  const a = (rashiA - 1) * 30 + degA;
  const b = (rashiB - 1) * 30 + degB;
  const d = Math.abs(a - b);
  return Math.min(d, 360.0 - d);
}

const mepRashi = (lagnaRashi, house) => ((lagnaRashi - 1 + (house - 1)) % 12) + 1;

export function mepOrb(graha, fromHouse, deg, rashi, targetHouse, mepDeg, lagnaRashi) {
  return mepOrbDetail(graha, fromHouse, deg, rashi, targetHouse, mepDeg, lagnaRashi)[0];
}

// See mep_orb / mep_orb_detail in the Python for the three mechanisms.
export function mepOrbDetail(graha, fromHouse, deg, rashi, targetHouse, mepDeg, lagnaRashi) {
  const targetMepRashi = mepRashi(lagnaRashi, targetHouse);
  const aspected = fmAspectedHouses(graha, fromHouse);
  let orb = absDiffDeg(rashi, deg, targetMepRashi, mepDeg);
  let via = fromHouse === targetHouse ? 'Conj.' : 'Cusp';
  for (const h of aspected) {
    if (h === fromHouse) continue;
    const cand = absDiffDeg(mepRashi(lagnaRashi, h), deg, targetMepRashi, mepDeg);
    if (cand < orb) { orb = cand; via = aspectAbbrev(graha, fromHouse, h) + ' (Cusp)'; }
  }
  if (aspected.has(targetHouse)) {
    const cand = Math.abs(deg - mepDeg);
    if (cand < orb) { orb = cand; via = aspectAbbrev(graha, fromHouse, targetHouse); }
  }
  return [orb, via];
}

export function aspectLabel(graha, fromHouse, toHouse) {
  if (fromHouse === toHouse) return 'conjunct';
  for (const off of ASPECT_OFFSETS[graha] || ASPECT_OFFSETS.default) {
    if (((fromHouse - 1 + off) % 12) + 1 === toHouse) {
      const n = off + 1;
      if (n === 2) return '2nd aspect';
      if (n === 3) return '3rd aspect';
      if (n === 4) return '4th aspect';
      return `${n}th aspect`;
    }
  }
  return 'aspect';
}

export function aspectAbbrev(graha, fromHouse, toHouse) {
  if (fromHouse === toHouse) return 'Conj.';
  for (const off of ASPECT_OFFSETS[graha] || ASPECT_OFFSETS.default) {
    if (((fromHouse - 1 + off) % 12) + 1 === toHouse) {
      const n = off + 1;
      return `${{ 1: '1st', 2: '2nd', 3: '3rd' }[n] || `${n}th`} Aspect`;
    }
  }
  return 'Cusp';
}

const isStrong = deg => deg >= 5.0 && deg <= 25.0;

function degStrength(deg) {
  if (deg >= 5.0 && deg <= 25.0) return 1.0;
  if (deg < 5.0) return deg / 5.0;
  return (30.0 - deg) / 5.0;
}

// Ra-Ke axis merge on a list of {fm, orb, …}: replaces the Rahu and Ketu
// entries with `merged(ra, ke)` at the front.
function mergeRaKe(list, merged) {
  const raI = list.findIndex(a => a.fm === 'Rahu');
  const keI = list.findIndex(a => a.fm === 'Ketu');
  if (raI < 0 || keI < 0) return null;
  const ra = list[raI], ke = list[keI];
  const ax = merged(ra, ke);
  list.splice(Math.max(raI, keI), 1);
  list.splice(Math.min(raI, keI), 1);
  list.unshift(ax);
  return ax;
}

// ─── analyze_all_grahas ────────────────────────────────────────────────────

export function analyzeAllGrahas(data) {
  const lr = data.lagna.rashi;
  const fms = new Set(FUNC_MALEFICS[lr] || []);
  const sunIsFm = fms.has('Sun');
  const mmp = MMP[lr];
  const mepDeg = data.lagna.degree_in_rashi;

  // D9 rashi lookup
  const d9Rashi = {};
  let d9Lagna = null;
  for (const dc of data.divisional_charts || []) {
    if (dc.chart_type === 'D9') {
      for (const g of dc.grahas || []) d9Rashi[g.graha] = g.rashi;
      if (dc.lagna) d9Lagna = dc.lagna.rashi;
      break;
    }
  }
  const hasD9 = n => n in d9Rashi;

  // Sun-like planets: lords of 2nd, 3rd, 9th houses that contain a mooltrikona sign
  const sunLikePlanets = new Set();
  for (const h of [2, 3, 9]) {
    const hr = ((lr - 1 + h - 1) % 12) + 1;
    const lord = MOOLA_LORD[hr];
    if (lord) sunLikePlanets.add(lord);
  }

  // Combustion
  const sunG = data.grahas.find(g => g.graha === 'Sun');
  const sunLon = sunG ? (sunG.rashi - 1) * 30 + sunG.degree_in_rashi : null;
  const combustSet = new Set();
  if (sunLon !== null) {
    for (const g of data.grahas) {
      const orb = COMBUST_ORB[g.graha];
      if (!orb) continue;
      const lon = (g.rashi - 1) * 30 + g.degree_in_rashi;
      let d = Math.abs(lon - sunLon);
      if (d > 180) d = 360 - d;
      if (d <= orb) combustSet.add(g.graha);
    }
  }

  // FM list
  const fmData = [];
  for (const g of data.grahas) {
    if (isNodeName(g.graha) || fms.has(g.graha)) {
      const house = ((g.rashi - lr + 12) % 12) + 1;
      fmData.push({ graha: g.graha, house, deg: g.degree_in_rashi, rashi: g.rashi });
    }
  }

  const inDust = (house, rashi, graha) => DUSHTANA.has(house) && MOOLA_LORD[rashi] !== graha;
  // Preliminary strength (states only), shared by chain detection and pass 1.
  function prelimOf(name, rashi, deg, house) {
    const debilitated = DEBI_RASHI[name] === rashi;
    const d9Debi = hasD9(name) && DEBI_RASHI[name] === d9Rashi[name];
    let prelim = deg;
    if (combustSet.has(name)) prelim *= sunIsFm ? 0.25 : 0.5;
    if (debilitated) prelim *= d9Debi ? 0.25 : 0.5;
    if (inDust(house, rashi, name)) prelim *= (d9Debi && !debilitated) ? 0.4 : 0.5;
    else if (d9Debi && !debilitated) prelim *= 0.75;
    return prelim;
  }

  const strongMap = {};
  for (const g of data.grahas) {
    strongMap[g.graha] = isNodeName(g.graha) ? false
      : prelimOf(g.graha, g.rashi, degStrength(g.degree_in_rashi), ((g.rashi - lr + 12) % 12) + 1) >= 0.70;
  }

  // Chain-special FMs (see the Python for the reasoning on nodes and MMP).
  const chainSpecial = {};
  for (const fm of fmData) {
    const targetStrong = isNodeName(fm.graha) ? true : get(strongMap, fm.graha, false);
    for (const src of fmData) {
      if (src.graha === fm.graha) continue;
      const srcIsNode = isNodeName(src.graha);
      const isConj = src.house === fm.house;
      if (!fmAspectedHouses(src.graha, src.house).has(fm.house)) continue;
      if (srcIsNode && !isConj) continue;
      const srcInDust = inDust(src.house, src.rashi, src.graha);
      const specialBase = src.graha === mmp || (srcIsNode && isConj) || srcInDust;
      const dmgOrbBase = !targetStrong ? 5 : (specialBase ? 2 : 1);
      if (Math.abs(src.deg - fm.deg) < dmgOrbBase) { chainSpecial[fm.graha] = src.graha; break; }
    }
  }

  // ── First pass: per-planet base analysis ──
  const analysis = {};
  for (const g of data.grahas) {
    const name = g.graha;
    const isNode = isNodeName(name);
    const house = ((g.rashi - lr + 12) % 12) + 1;
    const isFm = isNode || fms.has(name);
    const isMmp = name === mmp;
    const combust = combustSet.has(name);

    const degPct = isNode ? 1.0 : degStrength(g.degree_in_rashi);
    const weakByDeg = !isNode && !isStrong(g.degree_in_rashi);
    const debilitated = DEBI_RASHI[name] === g.rashi;
    const d9Debi = hasD9(name) && DEBI_RASHI[name] === d9Rashi[name];
    const exalted = EXALT_RASHI[name] === g.rashi;
    const inOwnMt = !isNode && MOOLA_RASHI[name] === g.rashi;
    const inSunLikeHouse = !isNode && [2, 3, 9].includes(house);
    const inLeo = !isNode && g.rashi === 5 && name !== 'Sun';
    const isSunLikePlanet = !isNode && name !== 'Sun' && sunLikePlanets.has(name);
    const d9Exalted = hasD9(name) && EXALT_RASHI[name] === d9Rashi[name];
    const d9House = d9Lagna !== null && hasD9(name) ? ((d9Rashi[name] - d9Lagna + 12) % 12) + 1 : null;
    const d9InDust = d9House !== null && DUSHTANA.has(d9House);
    const inDushtana = inDust(house, g.rashi, name);
    const dispositor = MOOLA_LORD[g.rashi] ?? null;

    const prelim = prelimOf(name, g.rashi, isNode ? 1.0 : degPct, house);
    const planetIsStrong = !isNode && prelim >= 0.70;

    // FM aspects to this planet
    let afflictions = [];
    let allFmAspects = [];
    for (const fm of fmData) {
      if (fm.graha === name) continue;
      if (isNode && isNodeName(fm.graha)) continue;
      if (!fmAspectedHouses(fm.graha, fm.house).has(house)) continue;
      const diff = Math.abs(fm.deg - g.degree_in_rashi);
      if (diff >= 5) continue;
      const via = aspectLabel(fm.graha, fm.house, house);
      const isNodeFm = isNodeName(fm.graha);
      const isConj = fm.house === house;
      const fmInDust = inDust(fm.house, fm.rashi, fm.graha);
      const special = fm.graha === mmp || (isNodeFm && isConj) || fmInDust;
      const cSpec = fm.graha in chainSpecial;
      const cSrc = chainSpecial[fm.graha] ?? null;
      const effSpec = special || cSpec;
      const dmgOrb = !planetIsStrong ? 5 : (effSpec ? 2 : 1);
      const isDmg = diff < dmgOrb;
      const dmgOrbBase = !planetIsStrong ? 5 : (special ? 2 : 1);
      const isDmgBase = diff < dmgOrbBase;
      allFmAspects.push({ fm: fm.graha, orb: diff, special, chainSpecial: cSpec, chainSource: cSrc,
        via, isDamaging: isDmg, dmgOrb, isDamagingBase: isDmgBase, isMmp: fm.graha === mmp, fmInDust });
      if (isDmg) {
        afflictions.push({ fm: fm.graha, orb: diff, special, chainSpecial: cSpec, chainSource: cSrc, via, dmgOrb });
      }
    }

    // FB aspects
    const fbAspects = [];
    for (const fb of data.grahas) {
      if (fb.graha === name || isNodeName(fb.graha) || fms.has(fb.graha)) continue;
      const fbHouse = ((fb.rashi - lr + 12) % 12) + 1;
      if (!fmAspectedHouses(fb.graha, fbHouse).has(house)) continue;
      const orb = Math.abs(fb.degree_in_rashi - g.degree_in_rashi);
      if (orb >= 5) continue;
      fbAspects.push({ fb: fb.graha, orb, via: aspectLabel(fb.graha, fbHouse, house) });
    }

    // Ra-Ke axis merge for allFmAspects / afflictions
    const ax = mergeRaKe(allFmAspects, (ra, ke) => ({
      fm: 'Ra-Ke', isRaKe: true,
      orb: Math.min(ra.orb, ke.orb),
      special: ra.special || ke.special,
      chainSpecial: ra.chainSpecial || ke.chainSpecial,
      chainSource: ra.chainSource || ke.chainSource,
      via: ra.orb <= ke.orb ? ra.via : ke.via,
      dmgOrb: ra.isDamaging ? ra.dmgOrb : ke.dmgOrb,
      isDamaging: ra.isDamaging || ke.isDamaging,
      isDamagingBase: get(ra, 'isDamagingBase', false) || get(ke, 'isDamagingBase', false),
      isMmp: get(ra, 'isMmp', null) || get(ke, 'isMmp', null),
      fmInDust: get(ra, 'fmInDust', null) || get(ke, 'fmInDust', null),
    }));
    if (ax) {
      afflictions = afflictions.filter(a => !isNodeName(a.fm));
      if (ax.isDamaging) {
        afflictions.unshift({ fm: 'Ra-Ke', isRaKe: true, orb: ax.orb, special: ax.special,
          chainSpecial: ax.chainSpecial, chainSource: ax.chainSource, via: ax.via, dmgOrb: ax.dmgOrb });
      }
    }

    // Condition 5: 2+ distinct FMs, each individually regular-damaging
    const cond5 = allFmAspects.filter(a => a.isDamagingBase).length >= 2;
    if (cond5) {
      for (const asp of allFmAspects) { asp.special = true; asp.cond5 = true; asp.isDamaging = true; }
      afflictions = allFmAspects.map(asp => ({ fm: asp.fm, orb: asp.orb, special: true,
        chainSpecial: asp.chainSpecial, chainSource: asp.chainSource,
        via: asp.via, dmgOrb: get(asp, 'dmgOrb', null), cond5: true, isRaKe: get(asp, 'isRaKe', null) }));
    }

    // MT house MEP afflictions
    const mtAff = [];
    const mtRashi = MOOLA_RASHI[name];
    if (mtRashi) {
      const mtHouse = ((mtRashi - lr + 12) % 12) + 1;
      const mtRaw = [];
      for (const fm of fmData) {
        if (fm.graha === name) continue;
        const [orb, via] = mepOrbDetail(fm.graha, fm.house, fm.deg, fm.rashi, mtHouse, mepDeg, lr);
        if (orb >= 5) continue;
        const isFc = fm.house === mtHouse;
        const spec = fm.graha === mmp || (isNodeName(fm.graha) && isFc)
          || inDust(fm.house, fm.rashi, fm.graha) || fm.graha in chainSpecial;
        mtRaw.push({ fm: fm.graha, orb, special: spec, inMtHouse: isFc, mtHouse, via });
      }
      mergeRaKe(mtRaw, (re, keE) => ({ fm: 'Ra-Ke', orb: Math.min(re.orb, keE.orb),
        special: true, inMtHouse: re.inMtHouse || keE.inMtHouse,
        mtHouse, isRaKe: true, via: re.orb <= keE.orb ? re.via : keE.via }));
      const mtC5 = mtRaw.length >= 2;
      for (const mta of mtRaw) {
        const s = mta.special || mtC5;
        let loss;
        if (s) loss = mta.orb < 2 ? 0.75 : 0.75 * (1 - (mta.orb - 2) / 3);
        else loss = mta.orb < 1 ? 0.75 : 0.75 * (1 - (mta.orb - 1) / 4);
        mtAff.push({ ...mta, loss, special: s, cond5: mtC5 });
      }
    }

    // House of occupation MEP afflictions
    const occAff = [];
    if (!isNode && MOOLA_RASHI[name] !== g.rashi) {
      const isMt = Boolean(MOOLA_LORD[g.rashi]);
      const occRaw = [];
      for (const fm of fmData) {
        const [orb, via] = mepOrbDetail(fm.graha, fm.house, fm.deg, fm.rashi, house, mepDeg, lr);
        if (orb >= 5) continue;
        const isFc2 = fm.house === house;
        const spec2 = fm.graha === mmp || (isNodeName(fm.graha) && isFc2)
          || inDust(fm.house, fm.rashi, fm.graha) || fm.graha in chainSpecial;
        occRaw.push({ fm: fm.graha, orb, special: spec2, isMtSign: isMt, via });
      }
      mergeRaKe(occRaw, (re, keE) => ({ fm: 'Ra-Ke', orb: Math.min(re.orb, keE.orb),
        special: true, isMtSign: isMt, isRaKe: true, via: re.orb <= keE.orb ? re.via : keE.via }));
      const occC5 = occRaw.length >= 2;
      for (const oa of occRaw) {
        const s = oa.special || occC5;
        let loss;
        if (isMt) {
          if (s) loss = oa.orb < 2 ? 0.75 : 0.75 * (1 - (oa.orb - 2) / 3);
          else loss = oa.orb < 1 ? 0.75 : 0.75 * (1 - (oa.orb - 1) / 4);
        } else {
          loss = (s ? 0.75 : 0.5) * (1 - oa.orb / 5);
        }
        occAff.push({ ...oa, loss, special: s, cond5: occC5 });
      }
    }

    const baseWeak = weakByDeg || combust || debilitated || inDushtana || cond5
      || afflictions.length > 0 || mtAff.length > 0 || occAff.length > 0;

    // Strength pipeline: states → MT house MEP → occ house MEP → direct FM
    let sp = isNode ? 1.0 : degPct;
    if (!isNode) {
      if (combust) sp *= sunIsFm ? 0.25 : 0.5;
      if (debilitated) sp *= d9Debi ? 0.25 : 0.5;
      if (inDushtana) sp *= (d9Debi && !debilitated) ? 0.4 : 0.5;
      else if (d9Debi && !debilitated) sp *= 0.75;
    }
    for (const mta of mtAff) sp *= (1 - mta.loss);
    for (const oa of occAff) sp *= (1 - oa.loss);
    if (!isNode) {
      if (cond5) {
        sp *= 0.25;
      } else {
        for (const aff of afflictions) {
          const baseLoss = planetIsStrong ? 0.5 : 0.75;
          if (planetIsStrong) sp *= (1 - baseLoss);
          else sp *= (1 - baseLoss * (1 - aff.orb / 5));
        }
      }
    }

    // Positive boosts (see the Python for the sun-like rules and sources)
    if (!isNode && exalted) sp *= 1.25;
    let mepHouseAfflicted;
    if (!isFm) mepHouseAfflicted = false;
    else if (inOwnMt) mepHouseAfflicted = false;
    else mepHouseAfflicted = occAff.some(a => a.orb < 1);
    let sunLikeBoost = false;
    if (inOwnMt) {
      sp *= 1.25; sunLikeBoost = true;
    } else {
      if (isSunLikePlanet) { sp *= 1.25; sunLikeBoost = true; }
      if (inSunLikeHouse && !mepHouseAfflicted) { sp *= 1.25; sunLikeBoost = true; }
    }
    if (inLeo && !mepHouseAfflicted) { sp *= 1.25; sunLikeBoost = true; }
    if (d9Exalted && !d9InDust) sp *= 1.25;

    analysis[name] = {
      graha: name, rashi: g.rashi,
      house, deg: g.degree_in_rashi, retro: get(g, 'retrograde', false),
      isFM: isFm, isMMP: isMmp, isNode,
      combust, weakByDeg,
      debilitated, d9Debilitated: d9Debi,
      exalted, inOwnMT: inOwnMt,
      d9Exalted, d9House, d9InDushtana: d9InDust,
      inDushtana,
      afflictions, allFmAspects,
      mtAfflictions: mtAff, occAfflictions: occAff,
      cond5, dispositor,
      degPct, strengthPct: sp,
      planetIsStrong, sunLikeBoost,
      isSunLikePlanet, inSunLikeHouse,
      inLeo, mepHouseAfflicted,
      fbAspects, fbBoostItems: [],
      baseWeak, dispositorWeak: false, dispCapped: false,
      isWeak: baseWeak, dispCapChain: [], degCapApplied: false,
    };
  }

  const planets = () => Object.values(analysis).filter(isPlanet);

  // ── FB boost pass (snapshot pre-boost so order doesn't matter) ──
  const preBoost = {};
  for (const a of planets()) preBoost[a.graha] = a.strengthPct;
  for (const a of planets()) {
    if (a.isNode) continue;
    for (const fba of a.fbAspects) {
      const fbStr = preBoost[fba.fb];
      if (fbStr === undefined) continue;
      const fbStrong = fbStr >= 0.70;
      let boost = 0.0;
      if (fbStrong) { if (fba.orb <= 5) boost = 0.5 * (1 - fba.orb / 5); }
      else if (fba.orb < 1) boost = 0.125 * (1 - fba.orb);
      if (boost <= 0) continue;
      a.strengthPct *= (1 + boost);
      a.fbBoostItems.push({ fb: fba.fb, orb: fba.orb, via: fba.via, boost, fbStrong });
    }
  }

  // ── Dispositor cap cascade (max 7 passes): always a ceiling; a weak
  // dispositor also marks the disposed planet weak ──
  for (let pass = 0; pass < 7; pass++) {
    let changed = false;
    for (const a of planets()) {
      if (!a.dispositor || a.dispositor === a.graha) continue;
      const disp = analysis[a.dispositor];
      if (!isPlanet(disp)) continue;
      if (disp.isWeak && !a.dispositorWeak) { a.dispositorWeak = true; a.isWeak = true; changed = true; }
      const cap = disp.strengthPct;
      if (cap < a.strengthPct) {
        a.strengthPct = cap;
        a.dispCapped = true;
        a.dispCapChain = [a.dispositor, ...disp.dispCapChain];
        changed = true;
      }
    }
    if (!changed) break;
  }

  // ── Update isWeak from final strengthPct ──
  for (const a of planets()) if (a.strengthPct >= 0.60) a.isWeak = false;

  // ── Degree cap: started below 100% (old age or infancy) → max 100% ──
  for (const a of planets()) {
    if (!a.isNode && a.degPct < 1.0 && a.strengthPct > 1.0) { a.strengthPct = 1.0; a.degCapApplied = true; }
  }

  // ── House strengths ──
  const houses = {};
  for (let h = 1; h <= 12; h++) {
    const hr = ((lr - 1 + h - 1) % 12) + 1;
    const mtLord = MOOLA_LORD[hr];
    if (mtLord) { houses[h] = { mt: true, rashi: hr, lord: mtLord }; continue; }
    let sp = 1.0;
    const boostsH = [], affH = [];
    // FB boosts to house
    for (const g of data.grahas) {
      if (isNodeName(g.graha) || fms.has(g.graha)) continue;
      const gh = ((g.rashi - lr + 12) % 12) + 1;
      const [orb, via] = mepOrbDetail(g.graha, gh, g.degree_in_rashi, g.rashi, h, mepDeg, lr);
      const an = analysis[g.graha];
      const ps = isPlanet(an) && get(an, 'strengthPct', 0) >= 0.70;
      let boost = 0.0;
      if (ps) { if (orb <= 5) boost = 0.5 * (1 - orb / 5); }
      else if (orb < 1) boost = 0.125 * (1 - orb);
      if (boost > 0) { sp += boost; boostsH.push({ planet: g.graha, orb, boost, via }); }
    }
    // FM afflictions to house (nodes special only when conjunct)
    for (const fm of fmData) {
      const [orb, via] = mepOrbDetail(fm.graha, fm.house, fm.deg, fm.rashi, h, mepDeg, lr);
      if (orb >= 5) continue;
      const isFmConj = fm.house === h;
      const isSp = fm.graha === mmp || (isNodeName(fm.graha) && isFmConj);
      const loss = (isSp ? 0.75 : 0.5) * (1 - orb / 5);
      if (loss <= 0) continue;
      sp -= loss;
      affH.push({ planet: fm.graha, orb, loss, isSpecial: isSp, isFMconj: isFmConj, via });
    }
    // Ra-Ke axis: single consolidated loss (special only if one node is conjunct)
    const onlyNodes = affH.length > 0 && affH.every(a => isNodeName(a.planet));
    let rkLoss = null;
    if (onlyNodes) {
      for (const a of affH) sp += a.loss;
      const rkOrb = Math.min(...affH.map(a => a.orb));
      const rkSpecial = affH.some(a => a.isFMconj);
      rkLoss = (rkSpecial ? 0.75 : 0.5) * (1 - rkOrb / 5);
      sp -= rkLoss;
    }
    sp = Math.max(sp, 0.0);
    houses[h] = { mt: false, rashi: hr, sp, boosts: boostsH, afflictions: affH, onlyNodes, rkLoss };
  }

  // ── Node strength = house strength of occupied sign ──
  for (const a of planets()) {
    if (!a.isNode) continue;
    const h = houses[a.house];
    if (!h) continue;
    let ns;
    if (h.mt) { const la = analysis[h.lord]; ns = isPlanet(la) ? la.strengthPct : 1.0; }
    else ns = Math.min(h.sp, 1.0);
    a.strengthPct = ns;
    a.isWeak = ns < 0.60;
  }

  analysis._houses = houses;
  analysis._mepDeg = mepDeg;
  analysis._sunIsFM = sunIsFm;
  return analysis;
}

// ─── screen_muhurta ────────────────────────────────────────────────────────

const fail = reason => ({ pass: false, reason });

export function screenMuhurta(data, analysis, cfg) {
  const lr = data.lagna.rashi;
  const fms = new Set(FUNC_MALEFICS[lr] || []);
  const mepDeg = data.lagna.degree_in_rashi;
  const lagnaRuler = LAGNA_RULER[lr];
  const exceptionsUsed = [];
  const planet = p => (isPlanet(analysis[p]) ? analysis[p] : null);

  const fmData = [];
  for (const g of data.grahas) {
    if (isNodeName(g.graha) || fms.has(g.graha)) {
      fmData.push({ graha: g.graha, house: ((g.rashi - lr + 12) % 12) + 1, deg: g.degree_in_rashi, rashi: g.rashi });
    }
  }

  // Rule 3b: per-planet minimum strength (lagna lord: max of lagnaLordMin and its own)
  const planetMins = get(cfg, 'planetMins', {});
  const lagnaLordMn = Number(truthy(get(cfg, 'lagnaLordMin', 0.60)) ? get(cfg, 'lagnaLordMin', 0.60) : 0);
  for (const p of MUHURTA_PLANETS) {
    let mn = Number(truthy(get(planetMins, p, 0)) ? get(planetMins, p, 0) : 0);
    if (p === lagnaRuler) {
      mn = Math.max(lagnaLordMn, mn);
      if (mn > 0) {
        const pa = planet(p);
        if (pa && get(pa, 'strengthPct', 1.0) < mn) {
          return fail(`Lagna lord ${p} strength ${pyRound(pa.strengthPct * 100)}% < ${pyRound(mn * 100)}% required`);
        }
      }
      continue;
    }
    if (mn > 0) {
      const pa = planet(p);
      if (pa && get(pa, 'strengthPct', 1.0) < mn) {
        return fail(`${p} strength ${pyRound(pa.strengthPct * 100)}% < ${pyRound(mn * 100)}% required`);
      }
    }
  }

  // Rule 4: any planet in dushtana
  const planetEntries = Object.values(analysis).filter(isPlanet);
  for (const a of planetEntries) if (a.inDushtana) return fail(`${a.graha} badly placed (h${a.house})`);

  // Rule 5a: special afflictions, each type individually allowable
  for (const a of planetEntries) {
    for (const asp of a.allFmAspects) {
      if (!((asp.special || asp.chainSpecial) && asp.isDamaging)) continue;
      const affLabel = truthy(asp.isRaKe) ? 'Ra-Ke' : asp.fm;
      let allowed = false;
      if (truthy(asp.isRaKe) && truthy(cfg.allowAffRaKe)) allowed = true;
      if (truthy(asp.isMmp) && truthy(cfg.allowAffMmp)) allowed = true;
      if (truthy(asp.fmInDust) && truthy(cfg.allowAffDust)) allowed = true;
      if (truthy(asp.chainSpecial) && truthy(cfg.allowAffChain)) allowed = true;
      if (truthy(asp.cond5) && truthy(cfg.allowAffCond5)) allowed = true;
      if (allowed) { exceptionsUsed.push(`Aff ${affLabel}→${a.graha}`); continue; }
      return fail(`Special affliction: ${affLabel} on ${a.graha}`);
    }
  }

  const mepHit = (fm, h) => mepOrb(fm.graha, fm.house, fm.deg, fm.rashi, h, mepDeg, lr);

  // Rule 5b: 2+ FMs afflict MEP of same MT sign house
  for (let h = 1; h <= 12; h++) {
    const hr = ((lr - 1 + h - 1) % 12) + 1;
    if (!MOOLA_LORD[hr]) continue;
    const seen = new Set();
    for (const fm of fmData) if (mepHit(fm, h) < 5) seen.add(fm.graha);
    if (seen.size >= 2) {
      if (truthy(cfg.allowRule5b)) exceptionsUsed.push(`2+ FMs on h${h} MEP (${[...seen].sort().join(', ')})`);
      else return fail(`2+ FMs afflict MT house ${h} MEP`);
    }
  }

  // Rule 5c: 1 FM afflicts MT sign house MEP AND that house's lord is afflicted
  const pAff = p => { const a = planet(p); return Boolean(a && a.allFmAspects && a.allFmAspects.length); };
  for (let h = 1; h <= 12; h++) {
    const hr = ((lr - 1 + h - 1) % 12) + 1;
    const hlord = MOOLA_LORD[hr];
    if (!hlord) continue;
    const hAff = fmData.some(fm => mepHit(fm, h) < 5);
    if (hAff && pAff(hlord)) {
      if (truthy(cfg.allowRule5c)) exceptionsUsed.push(`FM on h${h} MEP + ${hlord} afflicted`);
      else return fail(`FM afflicts h${h} MEP and ${hlord} is afflicted`);
    }
  }

  // Rule 5d: no FM within orb of the lagna lord, its MT sign MEP, or its occupied house MEP
  if (truthy(cfg.noFmLagna)) {
    const orb5d = 5;
    const llAn = planet(lagnaRuler);
    if (llAn) {
      for (const asp of llAn.allFmAspects || []) {
        if (asp.orb < orb5d) return fail(`FM ${asp.fm} within ${fmt1(asp.orb)}° of Lagna Lord ${lagnaRuler}`);
      }
    }
    let llMtHouse = null;
    for (const [rashi, lord] of Object.entries(MOOLA_LORD)) {
      if (lord === lagnaRuler) { llMtHouse = ((Number(rashi) - lr + 12) % 12) + 1; break; }
    }
    if (llMtHouse) {
      for (const fm of fmData) {
        const d = mepHit(fm, llMtHouse);
        if (d < orb5d) return fail(`FM ${fm.graha} aspects Lagna Lord MT sign (h${llMtHouse}) MEP within ${fmt1(d)}°`);
      }
    }
    const llGraha = data.grahas.find(g => g.graha === lagnaRuler);
    if (llGraha) {
      const llHouse = ((llGraha.rashi - lr + 12) % 12) + 1;
      for (const fm of fmData) {
        const d = mepHit(fm, llHouse);
        if (d < orb5d) return fail(`FM ${fm.graha} aspects Lagna Lord house (h${llHouse}) MEP within ${fmt1(d)}°`);
      }
    }
  }

  // Rule 6: active antardasha
  const chartDt = isoUs(data.birth_data.date + 'T' + data.birth_data.time);
  let activeAntar = null;
  for (const d of data.dasha || []) {
    if (activeAntar) break;
    for (const ad of d.antardasha || []) {
      if (isoUs(ad.start) <= chartDt && chartDt < isoUs(ad.end)) {
        activeAntar = { dasha: d.lord, antar: ad.lord, start: ad.start };
        break;
      }
    }
  }

  if (activeAntar) {
    const al = activeAntar.antar;
    if (isNodeName(al)) return fail(`Active antardasha ${al} is a node`);
    if (fms.has(al)) return fail(`Active antardasha ${al} is FM`);
    const aa = planet(al);
    const antarMin = Number(get(cfg, 'antarMin', 0.70));
    if (aa) {
      const pct = get(aa, 'strengthPct', 1.0);
      if (antarMin > 0 && pct < antarMin) {
        return fail(`Antardasha ${al} strength ${pyRound(pct * 100)}% < ${pyRound(antarMin * 100)}% required`);
      }
      if (pct < 0.70 && (antarMin === 0 || antarMin < 0.70)) exceptionsUsed.push(`Weak antar ${al} (${pyRound(pct * 100)}%)`);
    }
    if (aa && aa.inDushtana) return fail(`Active antardasha ${al} badly placed (h${aa.house})`);
  }

  // Benefic window: days from the chart date to the next node/FM antardasha
  let beneficDays = null;
  if (activeAntar) {
    let pastCurrent = false;
    outer:
    for (const d of data.dasha || []) {
      for (const ad of d.antardasha || []) {
        if (!pastCurrent) {
          if (isoUs(ad.start) <= chartDt && chartDt < isoUs(ad.end)) { pastCurrent = true; continue; }
          continue;
        }
        if (isNodeName(ad.lord) || fms.has(ad.lord)) {
          const day = s => Date.parse(s.slice(0, 10) + 'T00:00:00Z');
          beneficDays = Math.round((day(ad.start) - day(data.birth_data.date)) / 86400000);
          break outer;
        }
      }
    }
  }

  // Q1: Moon nakshatra lord must be FB
  const moonG = data.grahas.find(g => g.graha === 'Moon');
  if (!moonG) return fail('No Moon data');
  const moonLon = (moonG.rashi - 1) * 30 + moonG.degree_in_rashi;
  const nakIdx = Math.trunc(moonLon / (360 / 27));
  const nakLord = NAK_LORDS_27[Math.min(nakIdx, 26)];
  if (isNodeName(nakLord) || fms.has(nakLord)) return fail(`Moon nak lord ${nakLord} is FM/node`);

  // Q2: enough strong planets
  const sThresh = truthy(cfg.lowerStrongThreshold) ? 0.60 : 0.70;
  const countStrong = t => MUHURTA_PLANETS.filter(p => planet(p) && get(analysis[p], 'strengthPct', 0) >= t).length;
  const strongPlanets = countStrong(sThresh);
  const minSp = get(cfg, 'minStrongPlanets', 2);
  if (strongPlanets < minSp) return fail(`Only ${strongPlanets} strong planets (need ${minSp}+)`);
  if (truthy(cfg.lowerStrongThreshold) && countStrong(0.70) < minSp) {
    exceptionsUsed.push(`Low-strength planets counted (${strongPlanets} ≥60%)`);
  }

  // Q3: enough strong houses
  const houseMap = get(analysis, '_houses', {});
  const houseSp = hs => (hs.mt ? (planet(hs.lord) ? get(analysis[hs.lord], 'strengthPct', 0) : 0) : get(hs, 'sp', 0));
  const countHouses = t => { let n = 0; for (let h = 1; h <= 12; h++) { const hs = houseMap[h]; if (hs && houseSp(hs) >= t) n++; } return n; };
  const strongHouses = countHouses(sThresh);
  const minSh = get(cfg, 'minStrongHouses', 5);
  if (strongHouses < minSh) return fail(`Only ${strongHouses} strong houses (need ${minSh}+)`);
  if (truthy(cfg.lowerStrongThreshold) && countHouses(0.70) < minSh && !exceptionsUsed.some(e => e.includes('Low-strength'))) {
    exceptionsUsed.push(`Low-strength houses counted (${strongHouses} ≥60%)`);
  }

  // Benefic window filter
  const minBd = truthy(get(cfg, 'minBeneficDays', 0)) ? get(cfg, 'minBeneficDays', 0) : 0;
  if (minBd > 0 && (beneficDays === null || beneficDays < minBd)) {
    return fail(`Benefic window ${truthy(beneficDays) ? beneficDays : 0}d < ${minBd}d minimum`);
  }

  return {
    pass: true,
    strongPlanets,
    strongHouses,
    antarDasha: activeAntar ? activeAntar.dasha + '/' + activeAntar.antar : '?',
    antarStart: activeAntar ? activeAntar.start : null,
    beneficDays,
    exceptionsUsed,
  };
}
