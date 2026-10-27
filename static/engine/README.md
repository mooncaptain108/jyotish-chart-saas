# Offline chart engine

The chart calculations, in JavaScript, running in the browser with no
server. Shared by the web app (offline use) and the Android app
(jyotish-query-android, a Capacitor wrapper around `static/`).

- `engine.js`: port of the server's chart code (`config.py`,
  `calculations/ephemeris.py`, `grahas.py`, `lagna.py`, `bhavas.py`,
  `dasha.py`, `services/chart_service.py`). `initEngine()` then
  `computeChart(birthData)`, which returns the same fields as
  `POST /api/v1/chart` for what it covers.
- `vendor/sweph-wasm/`: Swiss Ephemeris 2.10.03 (the server's pyswisseph
  version) compiled to WebAssembly, from npm `sweph-wasm` 2.6.9 (AGPL-3.0).
- `ephe/sepl_18.se1`: planet data for 1800–2399, a copy of
  `ephemeris/sepl_18.se1`. Moshier (no file) shifts dasha dates by
  minutes, so the file is required.

Same settings as the server: Lahiri VP285 ayanamsa, true node, equal
houses.

## Parity with the server

`tests/engine-parity.spec.js` in the JyotishQuerySupport repo sends 61
charts (fixtures plus seeded random 1850–2099, latitudes ±65°,
fractional and negative time zones) to `/api/v1/chart` and to this
engine and requires them to match: positions to 0.0001°, every rashi,
nakshatra, pada and house, every dasha boundary within 1 ms. Every
module ported here gets the same check.

## Covered so far

Ayanamsa, lagna, bhavas, grahas, Vimshottari dasha (3 levels).

Still on the server: divisional charts, panchanga, ashtakavarga,
transits, muhurta search, time zone lookup, geocoding (online only).

When the phone is online: geocode new locations, and run Muhurta
searches on jyotish.allthisisthat.net if it is reachable.
