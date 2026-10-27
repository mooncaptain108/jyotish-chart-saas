// Time zones offline: ports of services/geocode_service.tz_offset_for_date
// (/api/v1/tz-offset), using the time zone database built into the browser
// (Intl) instead of pytz, and tz_names_for_points (/api/v1/tz-lookup), using
// the bundled @photostructure/tz-lookup map (88 KB) instead of
// timezonefinder. That map is approximate near borders, so prefer the server
// for lookups when it is reachable.
import tzlookup from './vendor/tz-lookup/tz-lookup.js';

const fmtCache = new Map();
function formatter(tz) {
  let f = fmtCache.get(tz);
  if (!f) {
    f = new Intl.DateTimeFormat('en-US', { timeZone: tz, timeZoneName: 'longOffset' });
    fmtCache.set(tz, f);
  }
  return f;
}

// UTC offset in hours of zone `tz` at the instant `utcMs`.
// Intl writes it as "GMT", "GMT+05:30" or, for local mean time, "GMT-07:52:58".
function offsetAt(tz, utcMs) {
  const name = formatter(tz).formatToParts(new Date(utcMs)).find(p => p.type === 'timeZoneName').value;
  const m = /GMT([+-])(\d{2}):(\d{2})(?::(\d{2}))?/.exec(name);
  if (!m) return 0;
  const h = Number(m[2]) + Number(m[3]) / 60 + Number(m[4] || 0) / 3600;
  return m[1] === '-' ? -h : h;
}

// Offset at local noon on `dateStr` (YYYY-MM-DD), the moment pytz uses, and
// whether daylight saving is in force then. Intl has no DST flag, so DST
// means "ahead of the zone's lower offset that year" (January vs July,
// which also covers the southern hemisphere).
export function tzOffsetForDate(tz, dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const noonUtc = Date.UTC(y, m - 1, d, 12);
  let utc = noonUtc;
  for (let i = 0; i < 3; i++) utc = noonUtc - offsetAt(tz, utc) * 3600e3;
  const offset = offsetAt(tz, utc);
  const std = Math.min(offsetAt(tz, Date.UTC(y, 0, 1, 12)), offsetAt(tz, Date.UTC(y, 6, 1, 12)));
  // pytz rounds offsets to whole minutes (matters only for pre-1900 local
  // mean time, e.g. Los Angeles -7:52:58 → -7:53).
  return { offset: Math.round(offset * 60) / 60, dst: offset > std };
}

// IANA zone name at a point, or null when out of range (as the server).
export function tzNameAt(lat, lon) {
  if (!(lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180)) return null;
  try { return tzlookup(lat, lon); } catch { return null; }
}
