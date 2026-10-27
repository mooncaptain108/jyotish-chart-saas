// Divisional charts (vargas) D1–D60: port of the server's
// calculations/divisional.py and constants/divisional_mappings.py.
// The sign rules carry hard-won fixes (D30 odd/even tables, D60
// forward-from-same-sign); see the docstrings there before changing any.

const rashiOf = lon => Math.floor(lon / 30) % 12 + 1;
const fromSign = (start, part) => (start - 1 + part) % 12 + 1;
const isOdd = r => r % 2 === 1;
// Starting sign by modality (movable / fixed / dual) or element
// (fire / earth / air / water).
const byModality = (r, mov, fix, dual) => [1, 4, 7, 10].includes(r) ? mov : [2, 5, 8, 11].includes(r) ? fix : dual;
const byElement = (r, fire, earth, air, water) =>
  [1, 5, 9].includes(r) ? fire : [2, 6, 10].includes(r) ? earth : [3, 7, 11].includes(r) ? air : water;

// D30 (span°, sign) per Parashara; odd and even signs differ.
const TRIMSAMSA_ODD = [[5, 1], [5, 11], [8, 9], [7, 3], [5, 7]];
const TRIMSAMSA_EVEN = [[5, 2], [7, 6], [8, 12], [5, 10], [5, 8]];

// Each rule: (rashi, degree-in-sign) → divisional sign. `n` is the number
// of equal divisions per sign (none for D30, which is unequal).
const VARGAS = {
  D1: { n: 1, sign: r => r },
  D2: { n: 2, sign: (r, d) => d < 15 ? (isOdd(r) ? 5 : 4) : (isOdd(r) ? 4 : 5) },
  D3: { n: 3, sign: (r, d) => d < 10 ? r : d < 20 ? fromSign(r, 4) : fromSign(r, 8) },
  D4: { n: 4, sign: (r, d) => fromSign(r, 3 * Math.floor(d / 7.5)) },
  D7: { n: 7, sign: (r, d) => fromSign(isOdd(r) ? r : fromSign(r, 6), Math.floor(d / (30 / 7))) },
  D8: { n: 8, sign: (r, d) => fromSign(byModality(r, 1, 9, 5), Math.floor(d / (30 / 8))) },
  D9: { n: 9, sign: (r, d) => fromSign(byElement(r, 1, 10, 7, 4), Math.floor(d / (30 / 9))) },
  D10: { n: 10, sign: (r, d) => fromSign(isOdd(r) ? r : fromSign(r, 8), Math.floor(d / 3)) },
  D12: { n: 12, sign: (r, d) => fromSign(r, Math.floor(d / 2.5)) },
  D16: { n: 16, sign: (r, d) => fromSign(byModality(r, 1, 5, 9), Math.floor(d / (30 / 16))) },
  D20: { n: 20, sign: (r, d) => fromSign(byModality(r, 1, 9, 5), Math.floor(d / 1.5)) },
  D24: { n: 24, sign: (r, d) => fromSign(isOdd(r) ? 5 : 4, Math.floor(d / 1.25)) },
  D27: { n: 27, sign: (r, d) => fromSign(byElement(r, 1, 4, 7, 10), Math.floor(d / (30 / 27))) },
  D30: {
    sign: (r, d) => {
      const table = isOdd(r) ? TRIMSAMSA_ODD : TRIMSAMSA_EVEN;
      let cum = 0;
      for (const [span, sign] of table) { cum += span; if (d < cum) return sign; }
      return table[table.length - 1][1];
    },
  },
  D40: { n: 40, sign: (r, d) => fromSign(isOdd(r) ? 1 : 7, Math.floor(d / 0.75)) },
  D45: { n: 45, sign: (r, d) => fromSign(byModality(r, 1, 5, 9), Math.floor(d / (30 / 45))) },
  D60: { n: 60, sign: (r, d) => fromSign(r, Math.floor(d / 0.5)) },
};

export const VARGA_TYPES = Object.keys(VARGAS);

function place(lon, v) {
  const sign = v.sign(rashiOf(lon), lon % 30);
  const deg = v.n ? (lon % 30 % (30 / v.n)) * v.n : null;
  return { sign, deg, lon: deg === null ? null : (sign - 1) * 30 + deg };
}

// planets: { Sun: { longitude }, … } in GRAHA_NAMES order.
export function computeDivisionalChart(planets, ascLon, chartType, grahaNames, rashiNames) {
  const v = VARGAS[chartType];
  if (!v) throw new Error(`Unsupported divisional chart: ${chartType}`);
  const l = place(ascLon, v);
  return {
    chart_type: chartType,
    lagna: { rashi: l.sign, rashi_name: rashiNames[l.sign], degree_in_rashi: l.deg, longitude: l.lon },
    grahas: grahaNames.map(g => {
      const p = place(planets[g].longitude, v);
      return { graha: g, rashi: p.sign, rashi_name: rashiNames[p.sign], degree_in_rashi: p.deg, longitude: p.lon };
    }),
  };
}
