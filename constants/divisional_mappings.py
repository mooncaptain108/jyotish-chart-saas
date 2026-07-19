"""Divisional chart (Varga) division rules.

Each divisional chart divides a sign into N equal parts.
The resulting sign is determined by the division rules below.
"""

# D2 (Hora): odd signs → Sun (Leo) / Moon (Cancer) based on half
# First half of odd sign → Leo (5), second half → Cancer (4)
# First half of even sign → Cancer (4), second half → Leo (5)

# D3 (Drekkana): 3 parts of 10° each
# Part 1 → same sign, Part 2 → 5th from it, Part 3 → 9th from it

# D30 (Trimsamsa) degree spans and resulting sign, per Parashara.
# Only the 5 non-luminous planets (Mars, Saturn, Jupiter, Mercury, Venus)
# rule any trimsamsa; each rules two signs across the zodiac, and which of
# its two signs applies DIFFERS between odd and even reckoning — e.g.
# Mercury's odd-sign portion maps to Gemini, but its even-sign portion
# maps to Virgo. The sign is stored directly (not the lord name) to avoid
# that ambiguity; a single lord-keyed lookup shared between odd/even was a
# real bug (verified against Sanjay Rath's published Trimsamsa table,
# https://srath.com/jyoti%E1%B9%A3a/varga/trimsamsa-d-30-chart/, 2026-07-19)
# that gave wrong signs for every planet landing in an even sign.
TRIMSAMSA_ODD = [
    (5, 1),    # 0–5°   Mars    -> Aries
    (5, 11),   # 5–10°  Saturn  -> Aquarius
    (8, 9),    # 10–18° Jupiter -> Sagittarius
    (7, 3),    # 18–25° Mercury -> Gemini
    (5, 7),    # 25–30° Venus   -> Libra
]

TRIMSAMSA_EVEN = [
    (5, 2),    # 0–5°   Venus   -> Taurus
    (7, 6),    # 5–12°  Mercury -> Virgo
    (8, 12),   # 12–20° Jupiter -> Pisces
    (5, 10),   # 20–25° Saturn  -> Capricorn
    (5, 8),    # 25–30° Mars    -> Scorpio
]
