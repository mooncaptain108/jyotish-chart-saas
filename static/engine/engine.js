// Offline chart engine — proof of concept.
//
// A JavaScript port of the server's chart calculations (jyotish-chart-saas:
// config.py, calculations/ephemeris.py, grahas.py, lagna.py, bhavas.py,
// dasha.py, panchanga.py, services/chart_service.py; divisional charts are
// in divisional.js), running Swiss Ephemeris compiled to
// WebAssembly (sweph-wasm, SE 2.10.03 — the same version as the server's
// pyswisseph). Output field names match the /api/v1/chart response so the
// parity test can compare them one to one.
import SwissEPH from './vendor/sweph-wasm/index.js';
import { computeDivisionalChart, VARGA_TYPES } from './divisional.js';

const GRAHA_NAMES = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
const RASHI_NAMES = [null, 'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya', 'Tula',
  'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];
const RASHI_LORDS = [null, 'Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus',
  'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
const NAKSHATRA_NAMES = [null, 'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
  'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
  'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Moola', 'Purva Ashadha',
  'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
  'Uttara Bhadrapada', 'Revati'];
// Birth-name sound for each nakshatra pada (shown with the lagna).
const PADA_SYLLABLES = [null,
  ['Chu', 'Che', 'Cho', 'Laa'], ['Lee', 'Loo', 'Le', 'Lo'], ['A', 'Ee', 'U', 'E'], ['O', 'Vaa', 'Vee', 'Vu'],
  ['Ve', 'Vo', 'Kaa', 'Kee'], ['Ku', 'Gha', 'Ing', 'Chha'], ['Ke', 'Ko', 'Haa', 'Hee'], ['Hu', 'He', 'Ho', 'Daa'],
  ['Dee', 'Doo', 'De', 'Do'], ['Maa', 'Mee', 'Moo', 'Me'], ['Mo', 'Taa', 'Tee', 'Too'], ['Te', 'To', 'Paa', 'Pee'],
  ['Poo', 'Sha', 'Na', 'Tha'], ['Pe', 'Po', 'Raa', 'Ree'], ['Roo', 'Re', 'Ro', 'Taa'], ['Tee', 'Too', 'Te', 'To'],
  ['Naa', 'Nee', 'Noo', 'Ne'], ['No', 'Yaa', 'Yee', 'Yoo'], ['Ye', 'Yo', 'Bhaa', 'Bhee'], ['Bhoo', 'Dhaa', 'Phaa', 'Dha'],
  ['Bhe', 'Bho', 'Jaa', 'Jee'], ['Khee', 'Khoo', 'Khe', 'Kho'], ['Gaa', 'Gee', 'Gu', 'Ge'], ['Go', 'Saa', 'See', 'Soo'],
  ['Se', 'So', 'Daa', 'Dee'], ['Doo', 'Tha', 'Jha', 'Yna'], ['De', 'Do', 'Cha', 'Chee']];
const GRAHA_SANSKRIT = { Sun: 'Surya', Moon: 'Chandra', Mars: 'Mangala', Mercury: 'Budha', Jupiter: 'Guru',
  Venus: 'Shukra', Saturn: 'Shani', Rahu: 'Rahu', Ketu: 'Ketu' };
const EXALTATION = { Sun: 1, Moon: 2, Mars: 10, Mercury: 6, Jupiter: 4, Venus: 12, Saturn: 7, Rahu: 3, Ketu: 9 };
const DEBILITATION = { Sun: 7, Moon: 8, Mars: 4, Mercury: 12, Jupiter: 10, Venus: 6, Saturn: 1, Rahu: 9, Ketu: 3 };
const OWN_SIGNS = { Sun: [5], Moon: [4], Mars: [1, 8], Mercury: [3, 6], Jupiter: [9, 12], Venus: [2, 7],
  Saturn: [10, 11], Rahu: [11], Ketu: [8] };
const dignity = (g, r) => EXALTATION[g] === r ? 'exalted' : DEBILITATION[g] === r ? 'debilitated'
  : OWN_SIGNS[g].includes(r) ? 'own_sign' : null;
const DASHA_SEQUENCE = [['Ketu', 7], ['Venus', 20], ['Sun', 6], ['Moon', 10], ['Mars', 7],
  ['Rahu', 18], ['Jupiter', 16], ['Saturn', 19], ['Mercury', 17]];
const DASHA_ORDER = DASHA_SEQUENCE.map(([n]) => n);
const DASHA_DURATIONS = Object.fromEntries(DASHA_SEQUENCE);
const VIMSHOTTARI_TOTAL_YEARS = 120;
const VARA_NAMES = ['Ravivara', 'Somavara', 'Mangalavara', 'Budhavara', 'Guruvara', 'Shukravara', 'Shanivara'];
const VARA_ENGLISH = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const TITHI_NAMES = ['Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami',
  'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
  'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami',
  'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya'];
const KARANA_FIXED = ['Kimstughna', 'Shakuni', 'Chatushpada', 'Nagava'];
const KARANA_REPEATING = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija', 'Vishti'];
const YOGA_NAMES = ['Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda', 'Sukarma',
  'Dhriti', 'Shula', 'Ganda', 'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra', 'Siddhi',
  'Vyatipata', 'Variyan', 'Parigha', 'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma',
  'Indra', 'Vaidhriti'];
const NAKSHATRA_SPAN = 360 / 27;
const PADA_SPAN = 360 / 108;

const rashiOf = lon => Math.floor(lon / 30) % 12 + 1;
const nakshatraOf = lon => Math.floor(lon / NAKSHATRA_SPAN) % 27 + 1;
const nakshatraLord = nak => DASHA_ORDER[(nak - 1) % 9];
const padaOf = lon => Math.floor((lon - (nakshatraOf(lon) - 1) * NAKSHATRA_SPAN) / PADA_SPAN) % 4 + 1;
const round = (x, n) => Math.round(x * 10 ** n) / 10 ** n;

let swe = null;
let FLAGS = 0;
let BODIES = null;

// Load the WebAssembly module and ephemeris data. `useMoshier` skips the data
// files and uses Swiss Ephemeris' built-in (slightly less precise) model.
export async function initEngine({ useMoshier = false } = {}) {
  swe = await SwissEPH.init();
  if (!useMoshier) await swe.swe_set_ephe_path(new URL('./ephe/', import.meta.url).href, ['sepl_18.se1']);
  swe.swe_set_sid_mode(swe.SE_SIDM_LAHIRI_VP285, 0, 0);
  FLAGS = swe.SEFLG_SIDEREAL | swe.SEFLG_SPEED | (useMoshier ? swe.SEFLG_MOSEPH : swe.SEFLG_SWIEPH);
  BODIES = { Sun: swe.SE_SUN, Moon: swe.SE_MOON, Mars: swe.SE_MARS, Mercury: swe.SE_MERCURY,
    Jupiter: swe.SE_JUPITER, Venus: swe.SE_VENUS, Saturn: swe.SE_SATURN, Rahu: swe.SE_TRUE_NODE };
  return swe.swe_version();
}

// Same as chart_service._parse_birth_input: local time → UT hour, with the
// day nudged by ±1 on rollover (julday copes with day 0 / day 32 itself).
function birthJd(dateStr, timeStr, tzOffset) {
  const [y, mo, d] = dateStr.split('-').map(Number);
  const [h, mi, s] = timeStr.split(':').map(Number);
  let utHour = h + mi / 60 + s / 3600 - tzOffset;
  let day = d;
  if (utHour < 0) { utHour += 24; day -= 1; } else if (utHour >= 24) { utHour -= 24; day += 1; }
  return swe.swe_julday(y, mo, day, utHour, swe.SE_GREG_CAL);
}

function computeAllPlanets(jd) {
  const pos = {};
  for (const [name, id] of Object.entries(BODIES)) {
    const r = swe.swe_calc_ut(jd, id, FLAGS);
    pos[name] = { longitude: r[0], latitude: r[1], speed_long: r[3] };
  }
  const ra = pos.Rahu;
  pos.Ketu = { longitude: (ra.longitude + 180) % 360, latitude: -ra.latitude, speed_long: ra.speed_long };
  return pos;
}

// bhavas.get_house_for_longitude
function houseOf(lon, cusps) {
  for (let i = 0; i < 12; i++) {
    const a = cusps[i], b = cusps[(i + 1) % 12];
    if (a < b ? (a <= lon && lon < b) : (lon >= a || lon < b)) return i + 1;
  }
  return Math.floor(((lon - cusps[0] + 360) % 360) / 30) + 1;
}

// ── Vimshottari dasha (dasha.py) ──
// Dates are kept as integer microseconds of a naive local datetime, the way
// Python's datetime + timedelta(days=float) does, so ISO strings match exactly.
const DAY_US = 86400e6;
const usToIso = us => {
  const ms = Math.floor(us / 1000), frac = us - ms * 1000;
  const iso = new Date(ms).toISOString().slice(0, 19);
  const micro = (ms % 1000 + 1000) % 1000 * 1000 + frac;
  return micro ? `${iso}.${String(micro).padStart(6, '0')}` : iso;
};
const addDays = (us, days) => us + Math.round(days * DAY_US);   // timedelta rounds to µs

function subPeriods(lord, startUs, durYears, levels) {
  const out = [];
  let cur = startUs;
  const i0 = DASHA_ORDER.indexOf(lord);
  for (let k = 0; k < 9; k++) {
    const sub = DASHA_ORDER[(i0 + k) % 9];
    const yrs = durYears * DASHA_DURATIONS[sub] / VIMSHOTTARI_TOTAL_YEARS;
    const end = addDays(cur, yrs * 365.25);
    const p = { lord: sub, start: usToIso(cur), end: usToIso(end), duration_years: round(yrs, 4) };
    if (levels >= 2) p.pratyantardasha = subPeriods(sub, cur, yrs, levels - 1);
    out.push(p);
    cur = end;
  }
  return out;
}

function computeMahadasha(moonLon, birthUs, levels = 3) {
  const nak = nakshatraOf(moonLon);
  const elapsed = (moonLon - (nak - 1) * NAKSHATRA_SPAN) / NAKSHATRA_SPAN;
  const i0 = DASHA_ORDER.indexOf(nakshatraLord(nak));
  const firstFull = DASHA_DURATIONS[DASHA_ORDER[i0]];
  const firstBalance = firstFull * (1 - elapsed);
  const periods = [];
  let cur = birthUs;
  for (let k = 0; k < 9; k++) {
    const lord = DASHA_ORDER[(i0 + k) % 9];
    const yrs = k === 0 ? firstBalance : DASHA_DURATIONS[lord];
    const end = addDays(cur, yrs * 365.25);
    const p = { lord, start: usToIso(cur), end: usToIso(end), duration_years: round(yrs, 4) };
    if (levels >= 2) {
      p.antardasha = k === 0
        // Birth mahadasha: antardashas run from the true (pre-birth) start.
        ? subPeriods(lord, addDays(birthUs, -(firstFull - firstBalance) * 365.25), firstFull, levels - 1)
        : subPeriods(lord, cur, yrs, levels - 1);
    }
    periods.push(p);
    cur = end;
  }
  return periods;
}

// ── Panchanga (panchanga.py) ──
// Upper-limb sunrise with refraction, as ephemeris.compute_sunrise. Where
// the Sun doesn't rise (polar day/night) pyswisseph hands back 0; the
// wrapper throws instead, so return 0 the same way.
function sunriseJd(jdUt, latitude, longitude) {
  try {
    return swe.swe_rise_trans(jdUt, swe.SE_SUN, null, swe.SEFLG_SWIEPH, swe.SE_CALC_RISE, [longitude, latitude, 0], 0, 0);
  } catch { return 0; }
}

function computePanchanga(sunLon, moonLon, jd, tz, latitude, longitude) {
  const diff = ((moonLon - sunLon) % 360 + 360) % 360;
  const tithi = Math.floor(diff / 12);
  const karana = Math.floor(diff / 6);
  const karanaName = karana === 0 ? KARANA_FIXED[0] : karana >= 57 ? KARANA_FIXED[karana - 56]
    : KARANA_REPEATING[(karana - 1) % 7];
  const yoga = Math.floor(((sunLon + moonLon) % 360) / (360 / 27));
  const nak = nakshatraOf(moonLon);

  // Vara runs sunrise to sunrise: born before sunrise → previous weekday.
  const localJd = jd + tz / 24;
  const localMidnightUt = Math.trunc(localJd + 0.5) - 0.5 - tz / 24;
  const srJd = sunriseJd(localMidnightUt, latitude, longitude);
  const varaIdx = Math.trunc((jd < srJd ? localJd - 1 : localJd) + 1.5) % 7;

  let srHours = swe.swe_revjul(srJd, swe.SE_GREG_CAL).hour + tz;
  if (srHours >= 24) srHours -= 24; else if (srHours < 0) srHours += 24;
  const h = Math.trunc(srHours), m = Math.trunc((srHours - h) * 60);
  const sec = Math.trunc(((srHours - h) * 60 - m) * 60);
  const p2 = n => String(n).padStart(2, '0');

  return {
    sunrise: `${p2(h)}:${p2(m)}:${p2(sec)}`,
    tithi: { number: tithi + 1, name: TITHI_NAMES[tithi], paksha: tithi < 15 ? 'Shukla' : 'Krishna' },
    karana: { number: karana + 1, name: karanaName },
    yoga: { number: yoga + 1, name: YOGA_NAMES[yoga] },
    nakshatra: { number: nak, name: NAKSHATRA_NAMES[nak], lord: nakshatraLord(nak), pada: padaOf(moonLon) },
    vara: { name: VARA_NAMES[varaIdx], english: VARA_ENGLISH[varaIdx] },
  };
}

// Planets, houses and lagna for a moment and place: shared by the natal
// chart and the transit positions.
function positionsAt(date, time, latitude, longitude, timezone_offset) {
  const jd = birthJd(date, time, timezone_offset);
  const planets = computeAllPlanets(jd);
  const { cusps: c13, ascmc } = swe.swe_houses_ex(jd, FLAGS, latitude, longitude, 'E');
  const cusps = c13.slice(1, 13);           // sweph-wasm returns cusps[1..12]
  const asc = ascmc[0];
  const lagna = {
    longitude: round(asc, 4), rashi: rashiOf(asc), rashi_name: RASHI_NAMES[rashiOf(asc)],
    degree_in_rashi: round(asc % 30, 4), nakshatra: nakshatraOf(asc),
    nakshatra_name: NAKSHATRA_NAMES[nakshatraOf(asc)], pada: padaOf(asc),
    pada_syllable: PADA_SYLLABLES[nakshatraOf(asc)][padaOf(asc) - 1],
  };
  const grahas = GRAHA_NAMES.map(g => {
    const { longitude: lon, speed_long: speed } = planets[g];
    const r = rashiOf(lon), n = nakshatraOf(lon);
    return {
      graha: g, graha_sanskrit: GRAHA_SANSKRIT[g], longitude: round(lon, 4), rashi: r, rashi_name: RASHI_NAMES[r], rashi_lord: RASHI_LORDS[r],
      degree_in_rashi: round(lon % 30, 4), nakshatra: n, nakshatra_name: NAKSHATRA_NAMES[n],
      nakshatra_lord: nakshatraLord(n), pada: padaOf(lon), house: houseOf(lon, cusps),
      retrograde: speed < 0 || g === 'Rahu' || g === 'Ketu', speed: round(speed, 6),
      dignity: dignity(g, r),
    };
  });
  return { jd, planets, cusps, asc, lagna, grahas, ayanamsa: round(swe.swe_get_ayanamsa_ut(jd), 6) };
}

// /api/v1/chart, minus ashtakavarga (the app doesn't use it).
export function computeChart({ name = null, date, time, latitude, longitude, timezone_offset }) {
  const { jd, planets, cusps, asc, lagna, grahas, ayanamsa } = positionsAt(date, time, latitude, longitude, timezone_offset);
  const bhavas = cusps.map((cl, i) => ({
    house: i + 1, cusp_longitude: round(cl, 4), rashi: rashiOf(cl),
    rashi_name: RASHI_NAMES[rashiOf(cl)], lord: RASHI_LORDS[rashiOf(cl)],
  }));
  const [y, mo, d] = date.split('-').map(Number);
  const [h, mi, s] = time.split(':').map(Number);
  const birthUs = Date.UTC(y, mo - 1, d, h, mi, s) * 1000;
  return {
    name,
    birth_data: { date, time, latitude, longitude, timezone_offset },
    ayanamsa, lagna, grahas, bhavas,
    divisional_charts: VARGA_TYPES.map(t => computeDivisionalChart(planets, asc, t, GRAHA_NAMES, RASHI_NAMES)),
    dasha: computeMahadasha(planets.Moon.longitude, birthUs, 3),
    panchanga: computePanchanga(planets.Sun.longitude, planets.Moon.longitude, jd, timezone_offset, latitude, longitude),
  };
}

// /api/v1/chart/transit: positions only. `grahas[i].house` is against this
// moment's own lagna; the app places transits by the natal lagna instead.
export function computeTransit({ date, time, latitude, longitude, timezone_offset }) {
  const { lagna, grahas, ayanamsa } = positionsAt(date, time, latitude, longitude, timezone_offset);
  return { birth_data: { date, time, latitude, longitude, timezone_offset }, ayanamsa, lagna, grahas };
}
