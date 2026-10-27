# Offline chart engine

The chart calculations, in JavaScript, running in the browser with no
server. Shared by the web app (offline use) and the Android app
(jyotish-query-android, a Capacitor wrapper around `static/`).

- `engine.js`: port of the server's chart code (`config.py`,
  `calculations/ephemeris.py`, `grahas.py`, `lagna.py`, `bhavas.py`,
  `dasha.py`, `panchanga.py`, `services/chart_service.py`).
  `initEngine()`, then `computeChart(birthData)` (= `POST /api/v1/chart`)
  and `computeTransit(birthData)` (= `POST /api/v1/chart/transit`).
- `divisional.js`: the 17 divisional charts (`calculations/divisional.py`).
- `tz.js`: `tzOffsetForDate(zone, date)` (= `GET /api/v1/tz-offset`, from
  the browser's own time zone database) and `tzNameAt(lat, lon)`
  (= `POST /api/v1/tz-lookup`, one point).
- `vendor/sweph-wasm/`: Swiss Ephemeris 2.10.03 (the server's pyswisseph
  version) compiled to WebAssembly, from npm `sweph-wasm` 2.6.9 (AGPL-3.0).
- `ephe/sepl_18.se1`: planet data for 1800–2399, a copy of
  `ephemeris/sepl_18.se1`. Moshier (no file) shifts dasha dates by
  minutes, so the file is required.
- `vendor/tz-lookup/`: npm `@photostructure/tz-lookup` 11.7.0 (CC0), an
  88 KB zone map, with `export default` added. Coarse near borders, so
  ask the server when it is reachable.

Same settings as the server: Lahiri VP285 ayanamsa, true node, equal
houses.

## Parity with the server

In the JyotishQuerySupport repo:

- `tests/engine-parity.spec.js` sends 61 charts (fixtures plus seeded
  random 1850–2099, latitudes ±65°, fractional and negative time zones)
  to `/api/v1/chart` and to this engine. Lagna, grahas and bhavas must be
  identical; divisional charts and panchanga too; every dasha boundary
  within 1 ms. Also 20 transit lookups, identical.
- `tests/engine-tz-parity.spec.js`: offsets identical for all 418 zones
  on dates 1925–2026 (pre-1900 local mean time differs in some zones; the
  display-only DST flag may differ for all-year war time and pytz's
  inverted Irish DST). Zone lookup: every atlas place, and over 95% of
  random land points (97% now).

Every module ported here gets the same check.

## Covered so far

Ayanamsa, lagna, bhavas, grahas, Vimshottari dasha (3 levels),
divisional charts, panchanga, transits, time zone offsets and lookup.

Still on the server: muhurta search; ashtakavarga (the app doesn't use
it); geocoding (online only).

When the phone is online: geocode new locations, and run Muhurta
searches on jyotish.allthisisthat.net if it is reachable.
