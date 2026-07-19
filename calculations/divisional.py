"""Divisional chart (Varga) calculations: D1–D60."""
from __future__ import annotations

from constants.rashis import longitude_to_rashi, RASHI_NAMES
from constants.divisional_mappings import TRIMSAMSA_ODD, TRIMSAMSA_EVEN


def _d1_sign(longitude: float) -> int:
    """D1 (Rashi chart) — same as birth rashi."""
    return longitude_to_rashi(longitude)


def _d2_sign(longitude: float) -> int:
    """D2 (Hora) — 2 divisions of 15° each.

    Odd sign: first half → Leo (5), second half → Cancer (4).
    Even sign: first half → Cancer (4), second half → Leo (5).
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    is_odd = rashi % 2 == 1

    if degree < 15:
        return 5 if is_odd else 4
    else:
        return 4 if is_odd else 5


def _d3_sign(longitude: float) -> int:
    """D3 (Drekkana) — 3 divisions of 10° each.

    Part 1 (0–10°): same sign
    Part 2 (10–20°): 5th from sign
    Part 3 (20–30°): 9th from sign
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30

    if degree < 10:
        return rashi
    elif degree < 20:
        return (rashi - 1 + 4) % 12 + 1  # 5th from sign
    else:
        return (rashi - 1 + 8) % 12 + 1  # 9th from sign


def _d4_sign(longitude: float) -> int:
    """D4 (Chaturthamsa) — 4 divisions of 7°30' each.

    Uniform for all signs: the four parts map to the 1st (same), 4th,
    7th and 10th signs from the sign (its kendras).
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / 7.5)  # 0–3
    return (rashi - 1 + 3 * part) % 12 + 1


def _d7_sign(longitude: float) -> int:
    """D7 (Saptamsa) — 7 divisions of 4°17'8.57" each.

    Odd sign: count from same sign.
    Even sign: count from 7th from sign.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / (30 / 7))  # 0–6
    is_odd = rashi % 2 == 1

    if is_odd:
        return (rashi - 1 + part) % 12 + 1
    else:
        return (rashi - 1 + 6 + part) % 12 + 1


def _d9_sign(longitude: float) -> int:
    """D9 (Navamsa) — 9 divisions of 3°20' each.

    The navamsa sign is determined by the absolute pada number.
    Each pada of 3°20' maps sequentially through the 12 signs,
    starting from Aries for fire signs, Cancer for water, Libra for air,
    Capricorn for earth.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / (30 / 9))  # 0–8

    # Starting sign based on element of rashi
    if rashi in (1, 5, 9):       # Fire
        start = 1
    elif rashi in (2, 6, 10):    # Earth
        start = 10
    elif rashi in (3, 7, 11):    # Air
        start = 7
    else:                         # Water (4, 8, 12)
        start = 4

    return (start - 1 + part) % 12 + 1


def _d10_sign(longitude: float) -> int:
    """D10 (Dasamsa) — 10 divisions of 3° each.

    Odd sign: count from same sign.
    Even sign: count from 9th from sign.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / 3)  # 0–9
    is_odd = rashi % 2 == 1

    if is_odd:
        return (rashi - 1 + part) % 12 + 1
    else:
        return (rashi - 1 + 8 + part) % 12 + 1


def _d12_sign(longitude: float) -> int:
    """D12 (Dwadasamsa) — 12 divisions of 2°30' each.

    Count from the same sign.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / 2.5)  # 0–11

    return (rashi - 1 + part) % 12 + 1


def _d16_sign(longitude: float) -> int:
    """D16 (Shodasamsa) — 16 divisions of 1°52'30" each.

    Movable signs count from Aries, fixed signs from Leo, dual signs
    from Sagittarius.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / (30 / 16))  # 0–15

    if rashi in (1, 4, 7, 10):      # Movable
        start = 1
    elif rashi in (2, 5, 8, 11):    # Fixed
        start = 5
    else:                            # Dual (3, 6, 9, 12)
        start = 9

    return (start - 1 + part) % 12 + 1


def _d20_sign(longitude: float) -> int:
    """D20 (Vimsamsa) — 20 divisions of 1°30' each.

    Movable signs count from Aries, fixed signs from Sagittarius, dual
    signs from Leo.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / 1.5)  # 0–19

    if rashi in (1, 4, 7, 10):      # Movable
        start = 1
    elif rashi in (2, 5, 8, 11):    # Fixed
        start = 9
    else:                            # Dual
        start = 5

    return (start - 1 + part) % 12 + 1


def _d24_sign(longitude: float) -> int:
    """D24 (Chaturvimsamsa / Siddhamsa) — 24 divisions of 1°15' each.

    Odd signs count from Leo, even signs from Cancer.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / 1.25)  # 0–23
    is_odd = rashi % 2 == 1
    start = 5 if is_odd else 4

    return (start - 1 + part) % 12 + 1


def _d27_sign(longitude: float) -> int:
    """D27 (Saptavimsamsa / Bhamsa) — 27 divisions of 1°6'40" each.

    Fire signs count from Aries, earth signs from Cancer, air signs
    from Libra, water signs from Capricorn. (Note: earth/water starts
    are swapped relative to D9's element mapping — this is a real
    classical distinction, not a copy-paste of D9.)
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / (30 / 27))  # 0–26

    if rashi in (1, 5, 9):          # Fire
        start = 1
    elif rashi in (2, 6, 10):       # Earth
        start = 4
    elif rashi in (3, 7, 11):       # Air
        start = 7
    else:                            # Water (4, 8, 12)
        start = 10

    return (start - 1 + part) % 12 + 1


def _d30_sign(longitude: float) -> int:
    """D30 (Trimsamsa) — unequal divisions based on Parashara's table.

    Odd signs and even signs have different division schemes, each
    listing (span, sign) pairs directly — see the constants module for
    why the sign can't be derived from the ruling planet alone.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    is_odd = rashi % 2 == 1

    table = TRIMSAMSA_ODD if is_odd else TRIMSAMSA_EVEN
    cumulative = 0
    for span, sign in table:
        cumulative += span
        if degree < cumulative:
            return sign

    # Fallback (should not reach here)
    return table[-1][1]


def _d40_sign(longitude: float) -> int:
    """D40 (Khavedamsa) — 40 divisions of 0°45' each.

    Odd signs count from Aries, even signs from Libra.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / 0.75)  # 0–39
    is_odd = rashi % 2 == 1
    start = 1 if is_odd else 7

    return (start - 1 + part) % 12 + 1


def _d45_sign(longitude: float) -> int:
    """D45 (Akshavedamsa) — 45 divisions of 0°40' each.

    Movable signs count from Aries, fixed signs from Leo, dual signs
    from Sagittarius (same starting-sign convention as D16, just a
    finer division).
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / (30 / 45))  # 0–44

    if rashi in (1, 4, 7, 10):      # Movable
        start = 1
    elif rashi in (2, 5, 8, 11):    # Fixed
        start = 5
    else:                            # Dual
        start = 9

    return (start - 1 + part) % 12 + 1


def _d60_sign(longitude: float) -> int:
    """D60 (Shashtiamsa) — 60 divisions of 0°30' each.

    Counts forward from the same sign for ALL signs — no odd/even
    asymmetry. 60 is a clean multiple of 12, so this cycles through all
    12 signs exactly 5 times within one 30° sign, always landing back on
    the sign itself at the start of each cycle.

    Two earlier versions of this function (both wrong) tried an odd/even
    split — first "backward from same sign" for even signs, then
    "forward from the 7th sign" for even signs. Both were shown wrong by
    concrete cross-checked data (Jupiter@Scorpio 28°46' and Saturn@Cancer
    27°15', verified 2026-07-19 against a reference app): only the
    unconditional forward-from-same-sign rule matched. What actually
    reverses between odd and even signs in classical D60 is the *deity
    name/nature* assigned to each of the 60 divisions (BPHS: a division
    inauspicious in odd signs is auspicious in even signs, and vice
    versa) — not the sign mapping. That deity-vs-sign distinction is
    almost certainly what got conflated into a sign-mapping "rule" in
    every secondhand web description checked, including the one this
    function was previously "fixed" against.
    """
    rashi = longitude_to_rashi(longitude)
    degree = longitude % 30
    part = int(degree / 0.5)  # 0–59

    return (rashi - 1 + part) % 12 + 1


# Dispatcher — full 16-varga shodasavarga set
_DIVISIONAL_FUNCS = {
    "D1": _d1_sign,
    "D2": _d2_sign,
    "D3": _d3_sign,
    "D4": _d4_sign,
    "D7": _d7_sign,
    "D9": _d9_sign,
    "D10": _d10_sign,
    "D12": _d12_sign,
    "D16": _d16_sign,
    "D20": _d20_sign,
    "D24": _d24_sign,
    "D27": _d27_sign,
    "D30": _d30_sign,
    "D40": _d40_sign,
    "D45": _d45_sign,
    "D60": _d60_sign,
}

# Divisions per sign for uniform chart types (D30 is non-uniform, excluded)
_DIVISIONAL_N = {
    "D1": 1,
    "D2": 2,
    "D3": 3,
    "D4": 4,
    "D7": 7,
    "D9": 9,
    "D10": 10,
    "D12": 12,
    "D16": 16,
    "D20": 20,
    "D24": 24,
    "D27": 27,
    "D40": 40,
    "D45": 45,
    "D60": 60,
}


def _divisional_degree(longitude: float, chart_type: str):
    """Compute degree_in_rashi (0-30) for uniform divisional charts.

    Returns None for D30 (Trimsamsa) which uses non-uniform segments.
    """
    n = _DIVISIONAL_N.get(chart_type)
    if n is None:
        return None
    degree = longitude % 30
    division_size = 30.0 / n
    return (degree % division_size) * n


def compute_divisional_chart(planet_positions: dict[str, dict],
                             ascendant_longitude: float,
                             chart_type: str = "D9") -> dict:
    """Compute a divisional chart for all grahas and lagna.

    Args:
        planet_positions: Output of ephemeris.compute_all_planets().
        ascendant_longitude: Sidereal longitude of the ascendant.
        chart_type: One of D1, D2, D3, D4, D7, D9, D10, D12, D16, D20,
            D24, D27, D30, D40, D45, D60.

    Returns:
        Dict with chart_type, lagna info, and list of graha placements.
    """
    func = _DIVISIONAL_FUNCS.get(chart_type)
    if func is None:
        raise ValueError(f"Unsupported divisional chart: {chart_type}")

    lagna_sign = func(ascendant_longitude)
    lagna_deg = _divisional_degree(ascendant_longitude, chart_type)
    lagna_lon = (lagna_sign - 1) * 30.0 + lagna_deg if lagna_deg is not None else None

    grahas = []
    from constants.grahas import GRAHA_NAMES
    for name in GRAHA_NAMES:
        lon = planet_positions[name]["longitude"]
        sign = func(lon)
        deg = _divisional_degree(lon, chart_type)
        div_lon = (sign - 1) * 30.0 + deg if deg is not None else None
        grahas.append({
            "graha": name,
            "rashi": sign,
            "rashi_name": RASHI_NAMES[sign],
            "degree_in_rashi": deg,
            "longitude": div_lon,
        })

    return {
        "chart_type": chart_type,
        "lagna": {
            "rashi": lagna_sign,
            "rashi_name": RASHI_NAMES[lagna_sign],
            "degree_in_rashi": lagna_deg,
            "longitude": lagna_lon,
        },
        "grahas": grahas,
    }


def compute_all_divisional_charts(planet_positions: dict[str, dict],
                                  ascendant_longitude: float) -> list[dict]:
    """Compute all 16 supported divisional charts (full shodasavarga)."""
    charts = []
    for chart_type in _DIVISIONAL_FUNCS:
        charts.append(
            compute_divisional_chart(planet_positions, ascendant_longitude, chart_type)
        )
    return charts
