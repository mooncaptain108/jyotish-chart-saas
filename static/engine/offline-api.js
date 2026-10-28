// The server's API, answered in the browser. index.html's apiFetch() sends
// a request here only when the server can't be reached; the answers have
// the same status codes and JSON as the server's, so the calling code
// doesn't know the difference.
import { initEngine, computeChart, computeTransit } from './engine.js';
import { analyzeAllGrahas, screenMuhurta, IDEAL_CFG } from './muhurta.js';
import { tzOffsetForDate, tzNameAt } from './tz.js';
import { startSearch } from './muhurta-search.js';

let ready = null;
const engine = () => (ready ??= initEngine());

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const detail = (msg, status = 400) => json({ detail: msg }, status);

// Muhurta searches started offline, by job id.
const jobs = new Map();
let jobSeq = 0;

// path: '/api/v1/...' with any query string; init: the fetch() options.
export async function handle(path, init = {}) {
  const url = new URL(path, 'http://offline');
  const p = url.pathname, method = (init.method || 'GET').toUpperCase();
  const body = () => JSON.parse(init.body || '{}');
  try {
    if (method === 'POST' && p === '/api/v1/chart') {
      await engine();
      const req = body();
      const chart = computeChart(req);
      if (req.include_analysis) chart.analysis = analyzeAllGrahas(chart);
      return json(chart);
    }
    if (method === 'POST' && p === '/api/v1/chart/transit') {
      await engine();
      return json(computeTransit(body()));
    }
    if (p === '/api/v1/tz-offset') {
      const zone = url.searchParams.get('iana_tz'), date = url.searchParams.get('date');
      return json({ timezone: zone, date, ...tzOffsetForDate(zone, date) });
    }
    if (method === 'POST' && p === '/api/v1/tz-lookup') {
      return json({ zones: body().points.map(pt => tzNameAt(pt.lat, pt.lon)) });
    }
    if (p === '/api/v1/geocode') {
      return detail('Place search needs an internet connection', 503);
    }
    if (p === '/api/v1/muhurta/ideal-cfg') return json(IDEAL_CFG);
    if (method === 'POST' && p === '/api/v1/muhurta/screen') {
      const { chart, cfg } = body();
      const analysis = analyzeAllGrahas(chart);
      return json({ analysis, screen: screenMuhurta(chart, analysis, cfg) });
    }
    if (method === 'POST' && p === '/api/v1/muhurta/search') {
      await engine();
      const id = `local-${Date.now().toString(36)}-${++jobSeq}`;
      jobs.set(id, startSearch(body()));
      return json({ job_id: id });
    }
    const m = /^\/api\/v1\/muhurta\/(status|results|search)\/(.+)$/.exec(p);
    if (m) {
      const [, kind, id] = m;
      const job = jobs.get(id);
      if (!job) {
        // A search the server was running when the connection dropped:
        // report it finished so the Muhurta dialog resets.
        if (kind === 'status') return json({ done: true, running: false, error: 'Lost connection to the server; search stopped' });
        if (kind === 'results') return json({ results: [] });
        return detail('Job not found', 404);
      }
      if (kind === 'status') return json(job.status());
      if (kind === 'results') return json({ results: job.results() });
      if (method === 'DELETE') { job.cancel(); return json({ cancelled: true }); }
    }
    return detail('Not available offline', 404);
  } catch (e) {
    return detail(String(e && e.message || e));
  }
}
