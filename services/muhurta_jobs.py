"""Background job management for server-side muhurta search.

Per-day parallelism via ProcessPoolExecutor: each day (all sign window searches +
per-minute scans) runs in its own worker process, bypassing the GIL.
Coarse 2-hour samples are shared across all selected signs within a day.
Job state stored in /tmp/jyotish_muhurta/{job_id}.json for cross-worker reads.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

from services.chart_service import _ensure_swisseph_initialized
from services.muhurta_analysis import RASHI_NAME

JOB_DIR     = '/tmp/jyotish_muhurta'
MAX_WORKERS = int(os.environ.get("MUHURTA_WORKERS", os.cpu_count() or 4))
os.makedirs(JOB_DIR, exist_ok=True)

# ─── File helpers ─────────────────────────────────────────────────────────────

def _job_path(job_id: str) -> str:
    return os.path.join(JOB_DIR, f'{job_id}.json')

def _read_job(job_id: str) -> dict | None:
    try:
        with open(_job_path(job_id)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def _write_job(job: dict) -> None:
    path = _job_path(job['id'])
    tmp  = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(job, f)
    os.replace(tmp, path)

# ─── Date / time helpers ───────────────────────────────────────────────────────

def _add_days(date_str: str, n: int) -> str:
    dt = datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=n)
    return dt.strftime('%Y-%m-%d')

def _minute_offset(base_date: str, add_mins: int) -> tuple[str, str]:
    total_min  = ((add_mins % 1440) + 1440) % 1440
    extra_days = add_mins // 1440
    dt = datetime.strptime(base_date, '%Y-%m-%d') + timedelta(days=extra_days)
    hh = str(total_min // 60).zfill(2)
    mm = str(total_min % 60).zfill(2)
    return dt.strftime('%Y-%m-%d'), f'{hh}:{mm}:00'

def _get_tz(tz_name: str | None, fixed_tz: float, date_str: str) -> float:
    if tz_name:
        from services.geocode_service import tz_offset_for_date
        return tz_offset_for_date(tz_name, date_str)['offset']
    return fixed_tz

# ─── Per-day worker (runs in subprocess) ──────────────────────────────────────

def _process_day(args: tuple) -> tuple[list, int]:
    """Process one full day for all target signs.
    Coarse 2-hour samples are computed once and reused across all signs.
    Returns (results_list, fetch_error_count).
    Runs in a subprocess — must import everything it needs.
    """
    (day_str, target_signs, lat, lon,
     tz_name, fixed_tz, cfg, loc_name,
     start_min, is_first_day) = args

    # Subprocess needs its own Swiss Ephemeris init
    from config import init_swisseph
    init_swisseph()
    from services.chart_service import compute_full_chart
    from services.muhurta_analysis import analyze_all_grahas, screen_muhurta, RASHI_NAME

    fetch_errors = 0

    def chart(d, t):
        tz = _get_tz(tz_name, fixed_tz, d)
        return compute_full_chart(None, d, t, lat, lon, tz)

    # ── 1. Coarse samples shared across all signs ──
    samples = []
    for m in range(0, 1440, 120):
        d, t = _minute_offset(day_str, m)
        try:
            data = chart(d, t)
        except Exception:
            fetch_errors += 1
            continue
        samples.append({'min': m, 'rashi': data['lagna']['rashi']})

    if not samples:
        return [], fetch_errors

    # ── 2. Per-sign: find window from coarse samples + binary search + minute scan ──
    all_results = []
    for target_sign in target_signs:
        # Find bracket from coarse samples (no extra calls)
        if samples[0]['rashi'] == target_sign:
            win_start = 0
        else:
            bl = bh = None
            for i in range(len(samples) - 1):
                if samples[i]['rashi'] != target_sign and samples[i+1]['rashi'] == target_sign:
                    bl, bh = samples[i]['min'], samples[i+1]['min']
                    break
            if bl is None:
                continue  # sign doesn't rise today

            lo, hi = bl, bh
            while hi - lo > 1:
                mid = (lo + hi) // 2
                d, t = _minute_offset(day_str, mid)
                try:
                    data = chart(d, t)
                except Exception:
                    fetch_errors += 1
                    break
                if data['lagna']['rashi'] == target_sign:
                    hi = mid
                else:
                    lo = mid
            win_start = hi

        scan_start = max(win_start, start_min) if is_first_day else win_start

        # Per-minute scan for this sign
        m = scan_start
        while m < 1440:
            d, t = _minute_offset(day_str, m)
            try:
                data = chart(d, t)
            except Exception:
                fetch_errors += 1
                break

            if data['lagna']['rashi'] != target_sign:
                break

            analysis = analyze_all_grahas(data)
            result   = screen_muhurta(data, analysis, cfg)

            if result['pass']:
                all_results.append({
                    'dt':             d + ' ' + t[:5],
                    'loc':            loc_name,
                    'sign':           target_sign,
                    'signName':       RASHI_NAME[target_sign] if target_sign < len(RASHI_NAME) else '',
                    'antarDasha':     result.get('antarDasha'),
                    'antarStart':     result.get('antarStart'),
                    'beneficDays':    result.get('beneficDays'),
                    'strongPlanets':  result.get('strongPlanets'),
                    'strongHouses':   result.get('strongHouses'),
                    'exceptionsUsed': result.get('exceptionsUsed', []),
                })
            m += 1

    return all_results, fetch_errors

# ─── Main search loop (background thread) ─────────────────────────────────────

def _run_search(job_id: str) -> None:
    """Runs in a background thread. Dispatches batches of days to a ProcessPool."""
    _ensure_swisseph_initialized()

    job = _read_job(job_id)
    if not job:
        return

    p            = job['params']
    cfg          = p['cfg']
    lat, lon     = float(p['lat']), float(p['lon'])
    tz_name      = p.get('tzName') or None
    fixed_tz     = float(p.get('tz', 0))
    start_date   = p['date']
    days         = int(p['days'])
    target_signs = list(p.get('targetSigns', [3]))
    start_min    = sum(int(x) * m for x, m in
                       zip((p.get('time', '00:00') + ':00').split(':'), [60, 1]))
    loc_name     = p.get('locName', '')

    all_results:  list[dict] = []
    fetch_errors: int        = 0
    last_day_str: str        = ''
    start_time  = time.time()

    try:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
            batch_start = 0
            while batch_start < days:
                # Check abort between batches
                fresh = _read_job(job_id)
                if fresh and fresh.get('abort'):
                    break

                batch_end = min(batch_start + MAX_WORKERS, days)
                batch_args = []
                for day in range(batch_start, batch_end):
                    day_str = _add_days(start_date, day)
                    batch_args.append((
                        day_str, target_signs, lat, lon,
                        tz_name, fixed_tz, cfg, loc_name,
                        start_min, day == 0,
                    ))

                # Run batch in parallel; map preserves order
                batch_results = list(pool.map(_process_day, batch_args))

                for i, (day_results, day_errs) in enumerate(batch_results):
                    all_results.extend(day_results)
                    fetch_errors += day_errs
                    last_day_str = _add_days(start_date, batch_start + i)

                batch_start = batch_end
                elapsed = time.time() - start_time
                job['dayCurrent']    = batch_end
                job['dayCurrentStr'] = last_day_str
                job['lastDayStr']    = last_day_str
                job['fetchErrors']   = fetch_errors
                job['elapsed']       = elapsed
                job['results']       = all_results
                job['resultCount']   = len(all_results)
                _write_job(job)

    except Exception as e:
        job['error'] = str(e)

    finally:
        # Final sort: Gemini results by dt first, then all other signs by dt
        gemini = sorted([r for r in all_results if r['sign'] == 3], key=lambda r: r['dt'])
        others = sorted([r for r in all_results if r['sign'] != 3], key=lambda r: r['dt'])
        final_results = gemini + others

        job['running']     = False
        job['done']        = True
        job['elapsed']     = time.time() - start_time
        job['fetchErrors'] = fetch_errors
        job['lastDayStr']  = last_day_str
        job['results']     = final_results
        job['resultCount'] = len(final_results)
        _write_job(job)

# ─── Public API ───────────────────────────────────────────────────────────────

def start_search(params: dict) -> str:
    job_id = uuid.uuid4().hex
    job = {
        'id':            job_id,
        'params':        params,
        'running':       True,
        'done':          False,
        'abort':         False,
        'error':         None,
        'results':       [],
        'resultCount':   0,
        'dayCurrent':    0,
        'dayTotal':      params['days'],
        'dayCurrentStr': '',
        'lastDayStr':    '',
        'fetchErrors':   0,
        'startTime':     time.time(),
        'elapsed':       0.0,
    }
    _write_job(job)
    t = threading.Thread(target=_run_search, args=(job_id,), daemon=True)
    t.start()
    return job_id

def get_status(job_id: str) -> dict | None:
    job = _read_job(job_id)
    if not job:
        return None
    return {k: v for k, v in job.items() if k not in ('results', 'params')}

def get_results(job_id: str) -> list | None:
    job = _read_job(job_id)
    return None if job is None else job.get('results', [])

def cancel_job(job_id: str) -> bool:
    job = _read_job(job_id)
    if not job:
        return False
    job['abort'] = True
    _write_job(job)
    return True
