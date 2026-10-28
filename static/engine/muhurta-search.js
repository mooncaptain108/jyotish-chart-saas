// Muhurta search offline: port of services/muhurta_jobs.py. Each day runs
// in a Web Worker (muhurta-worker.js), several at once, like the server's
// process pool. startSearch() reports progress in the same shape as
// GET /api/v1/muhurta/status, and results as GET /muhurta/results.
import { computeChart } from './engine.js';
import { analyzeAllGrahas, screenMuhurta, RASHI_NAME } from './muhurta.js';
import { tzOffsetForDate } from './tz.js';

// ─── Date / time helpers ───────────────────────────────────────────────────

const ymd = ms => new Date(ms).toISOString().slice(0, 10);
const dayMs = dateStr => Date.parse(dateStr + 'T00:00:00Z');
export const addDays = (dateStr, n) => ymd(dayMs(dateStr) + n * 86400000);

// _minute_offset: minutes past midnight of base date → (date, 'HH:MM:00')
function minuteOffset(baseDate, addMins) {
  const totalMin = ((addMins % 1440) + 1440) % 1440;
  const extraDays = Math.floor(addMins / 1440);
  const p2 = n => String(n).padStart(2, '0');
  return [addDays(baseDate, extraDays), `${p2(Math.floor(totalMin / 60))}:${p2(totalMin % 60)}:00`];
}

const tzFor = (tzName, fixedTz, dateStr) => (tzName ? tzOffsetForDate(tzName, dateStr).offset : fixedTz);

// ─── One day (_process_day) ────────────────────────────────────────────────
// Coarse 2-hour samples are shared by all target signs; per sign, binary
// search for the minute it rises, then screen every minute while it holds.
// Needs initEngine() to have run in this thread.
export function processDay({ dayStr, targetSigns, lat, lon, tzName, fixedTz, cfg, locName, startMin, isFirstDay }) {
  let fetchErrors = 0;
  const chart = (d, t) => computeChart({ date: d, time: t, latitude: lat, longitude: lon,
    timezone_offset: tzFor(tzName, fixedTz, d) }, { lean: true });

  // 1. Coarse samples shared across all signs
  const samples = [];
  for (let m = 0; m < 1440; m += 120) {
    const [d, t] = minuteOffset(dayStr, m);
    try { samples.push({ min: m, rashi: chart(d, t).lagna.rashi }); } catch { fetchErrors++; }
  }
  if (!samples.length) return { results: [], fetchErrors };

  // 2. Per sign: window from the samples, binary search, minute scan
  const results = [];
  for (const targetSign of targetSigns) {
    let winStart;
    if (samples[0].rashi === targetSign) {
      winStart = 0;
    } else {
      let bl = null, bh = null;
      for (let i = 0; i < samples.length - 1; i++) {
        if (samples[i].rashi !== targetSign && samples[i + 1].rashi === targetSign) {
          bl = samples[i].min; bh = samples[i + 1].min; break;
        }
      }
      if (bl === null) continue;            // sign doesn't rise today
      let lo = bl, hi = bh;
      while (hi - lo > 1) {
        const mid = Math.floor((lo + hi) / 2);
        const [d, t] = minuteOffset(dayStr, mid);
        let data;
        try { data = chart(d, t); } catch { fetchErrors++; break; }
        if (data.lagna.rashi === targetSign) hi = mid; else lo = mid;
      }
      winStart = hi;
    }

    let m = isFirstDay ? Math.max(winStart, startMin) : winStart;
    while (m < 1440) {
      const [d, t] = minuteOffset(dayStr, m);
      let data;
      try { data = chart(d, t); } catch { fetchErrors++; break; }
      if (data.lagna.rashi !== targetSign) break;
      const result = screenMuhurta(data, analyzeAllGrahas(data), cfg);
      if (result.pass) {
        results.push({
          dt: d + ' ' + t.slice(0, 5),
          loc: locName,
          sign: targetSign,
          signName: targetSign < RASHI_NAME.length ? RASHI_NAME[targetSign] : '',
          antarDasha: result.antarDasha ?? null,
          antarStart: result.antarStart ?? null,
          beneficDays: result.beneficDays ?? null,
          strongPlanets: result.strongPlanets ?? null,
          strongHouses: result.strongHouses ?? null,
          exceptionsUsed: result.exceptionsUsed ?? [],
        });
      }
      m++;
    }
  }
  return { results, fetchErrors };
}

// Final order, as the server: Gemini results by time, then all other signs.
export const sortResults = rs => [
  ...rs.filter(r => r.sign === 3).sort((a, b) => (a.dt < b.dt ? -1 : a.dt > b.dt ? 1 : 0)),
  ...rs.filter(r => r.sign !== 3).sort((a, b) => (a.dt < b.dt ? -1 : a.dt > b.dt ? 1 : 0)),
];

// ─── The search (_run_search) ──────────────────────────────────────────────
// params: the POST /api/v1/muhurta/search body ({ lat, lon, tz, tzName,
// locName, date, time, days, targetSigns | targetSign, cfg }).
// Returns { status(), results(), cancel(), done } — `done` resolves with the
// final status once every day has finished or the search was cancelled.
export function startSearch(params, { workers = defaultWorkers(), onProgress } = {}) {
  const targetSigns = params.targetSigns && params.targetSigns.length
    ? params.targetSigns.map(Number) : [params.targetSign != null ? Number(params.targetSign) : 3];
  const days = Number(params.days);
  const startMin = (params.time || '00:00').split(':').slice(0, 2).reduce((m, x, i) => m + Number(x) * [60, 1][i], 0);
  const base = {
    targetSigns, lat: Number(params.lat), lon: Number(params.lon),
    tzName: params.tzName || null, fixedTz: Number(params.tz || 0),
    cfg: params.cfg, locName: params.locName || '', startMin,
  };

  const startTime = Date.now();
  let all = [];
  const st = {
    running: true, done: false, abort: false, error: null, resultCount: 0,
    dayCurrent: 0, dayTotal: days, dayCurrentStr: '', lastDayStr: '',
    fetchErrors: 0, startTime: startTime / 1000, elapsed: 0,
  };

  let next = 0, finish;
  const done = new Promise(res => { finish = res; });
  const pool = [];
  const end = () => {
    pool.forEach(w => w.terminate());
    all = sortResults(all);
    Object.assign(st, { running: false, done: true, resultCount: all.length, elapsed: (Date.now() - startTime) / 1000 });
    onProgress?.({ ...st });
    finish({ ...st });
  };
  const feed = w => {
    if (st.abort || next >= days) {
      w.idle = true;
      if (pool.every(x => x.idle)) end();
      return;
    }
    const day = next++;
    w.postMessage({ ...base, dayStr: addDays(params.date, day), isFirstDay: day === 0, day });
  };

  for (let i = 0; i < Math.min(workers, days); i++) {
    const w = new Worker(new URL('./muhurta-worker.js', import.meta.url), { type: 'module' });
    w.onmessage = ({ data: msg }) => {
      if (msg.error) st.fetchErrors++;
      else { all.push(...msg.results); st.fetchErrors += msg.fetchErrors; }
      st.dayCurrent++;
      st.dayCurrentStr = st.lastDayStr = addDays(params.date, msg.day);
      st.resultCount = all.length;
      st.elapsed = (Date.now() - startTime) / 1000;
      onProgress?.({ ...st });
      feed(w);
    };
    w.onerror = e => { st.error = e.message || 'worker failed'; st.abort = true; w.idle = true; if (pool.every(x => x.idle)) end(); };
    pool.push(w);
  }
  pool.forEach(feed);
  if (!pool.length) end();

  return {
    status: () => ({ ...st }),
    results: () => all.slice(),
    cancel: () => { st.abort = true; },
    done,
  };
}

function defaultWorkers() {
  const n = (typeof navigator !== 'undefined' && navigator.hardwareConcurrency) || 4;
  return Math.max(1, Math.min(8, n - 1));
}
