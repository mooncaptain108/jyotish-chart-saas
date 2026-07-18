"""Tests for services/muhurta_analysis.py — strength analysis and muhurta screening.

These pin down behavior confirmed against the JS implementation during the
2026-07 consolidation work: sun-like boosts, the degree cap, FM self-affliction
of an occupied house, the combined aspect-projection/physical-adjacency MEP
orb formula, and Rule 5d. See house_boundary_mep_fix / followup_js_python_dup
memory notes for background on why these specific behaviors matter.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.muhurta_analysis import analyze_all_grahas, screen_muhurta, mep_orb


def _chart(lagna_rashi, lagna_deg, grahas):
    """Build a minimal chart dict analyze_all_grahas/screen_muhurta can consume.
    grahas: dict of name -> (rashi, degree_in_rashi)."""
    return {
        'lagna': {'rashi': lagna_rashi, 'degree_in_rashi': lagna_deg},
        'grahas': [
            {'graha': name, 'rashi': rashi, 'degree_in_rashi': deg, 'retrograde': False}
            for name, (rashi, deg) in grahas.items()
        ],
        'birth_data': {'date': '2026-01-01', 'time': '00:00:00'},
        'dasha': [],
    }


# ─── mep_orb: combined aspect-projection + physical-boundary-adjacency ────

def test_mep_orb_aspect_projection_case():
    """Mars in house7 (Aries rising) at 9:08 aspecting MEP(2) at 7:58 should
    resolve via the aspect-projection mechanism (plain degree distance),
    not the physical/rashi-aware one — real user-reported case."""
    lr = 1
    mars_rashi = ((7 - 1 + lr - 1) % 12) + 1
    orb = mep_orb('Mars', 7, 9 + 8/60, mars_rashi, 2, 7 + 58/60, lr)
    assert abs(orb - 1.1667) < 0.001


def test_mep_orb_physical_boundary_case():
    """Rahu at 29:58 in house2 bleeding into MEP(3) at 0:22 — no classical
    aspect involved, must resolve via the rashi-aware physical mechanism."""
    lr = 1
    rahu_rashi = ((2 - 1 + lr - 1) % 12) + 1
    orb = mep_orb('Rahu', 2, 29 + 58/60, rahu_rashi, 3, 0 + 22/60, lr)
    assert abs(orb - 0.4) < 0.001


# ─── Sun-like boosts ────────────────────────────────────────────────────

def test_sun_like_house_boost_alone():
    """A planet occupying house 2/3/9 (but not itself a sun-like lord) gets
    exactly +25%, no more. Minimal 2-planet chart -- no dispositor/FB/MT
    interference (Taurus rising, Venus alone in house2/Gemini)."""
    chart = _chart(2, 15.0, {
        'Sun': (9, 15.0),        # safe house, keeps combustion/dispositor checks inert
        'Venus': (3, 20.0),      # house2 (Gemini) -- sun-like house, not a sun-like lord
    })
    an = analyze_all_grahas(chart)
    v = an['Venus']
    assert v['inSunLikeHouse'] is True
    assert v['isSunLikePlanet'] is False
    assert abs(v['strengthPct'] - 1.25) < 0.001


def test_sun_like_boosts_stack_independently():
    """A planet that is both a sun-like lord AND in its own sign (Leo) gets
    both boosts, multiplicatively (Aries rising: Jupiter lords house9's
    Sagittarius MT sign, and here sits in Leo -- inLeo -- but not in a
    sun-like house itself)."""
    chart = _chart(1, 15.0, {
        'Sun': (4, 15.0),        # safe house, keeps Jupiter's dispositor strong
        'Jupiter': (5, 8.0),     # Leo, house5 -- not a sun-like house
    })
    an = analyze_all_grahas(chart)
    j = an['Jupiter']
    assert j['isSunLikePlanet'] is True
    assert j['inLeo'] is True
    assert j['inSunLikeHouse'] is False
    assert abs(j['strengthPct'] - 1.5625) < 0.001


def test_sun_like_boost_suppressed_by_mep_affliction():
    """Placement-based sun-like boosts (own-MT/sun-like-house/Leo) are
    suppressed when an FM afflicts the occupied house's MEP within 1°,
    but isSunLikePlanet is never suppressed."""
    # Mercury (FM for Aries) in house2 at the same degree as the ascendant
    # -> self-afflicts its own occupied house MEP (orb ~0), suppressing
    # the inSunLikeHouse boost.
    chart = _chart(1, 10.0, {
        'Sun': (5, 10.0), 'Moon': (8, 10.0), 'Mars': (9, 10.0),
        'Mercury': (2, 10.0), 'Jupiter': (9, 10.0), 'Venus': (9, 10.0),
        'Saturn': (12, 10.0), 'Rahu': (5, 10.0), 'Ketu': (11, 10.0),
    })
    an = analyze_all_grahas(chart)
    m = an['Mercury']
    assert m['inSunLikeHouse'] is True
    assert m['mepHouseAfflicted'] is True
    assert m['sunLikeBoost'] is False


# ─── Degree cap ─────────────────────────────────────────────────────────

def test_degree_cap_applies_when_boosts_exceed_100pct():
    """A planet that started below 100% on raw degree strength cannot be
    boosted above 100% even after stacking sun-like/exaltation boosts."""
    # Leo rising: house2 = Virgo (Mercury's exaltation AND a sun-like house
    # AND Mercury is itself house2's lord -> triple stack).
    chart = _chart(5, 10.0, {
        'Sun': (5, 14.0), 'Moon': (8, 13.0), 'Mars': (1, 15.0),
        'Mercury': (6, 4.0),  # Virgo, degPct=0.8, exalted, sun-like house+lord
        'Jupiter': (9, 20.0), 'Venus': (7, 17.0), 'Saturn': (12, 18.0),
        'Rahu': (3, 19.0), 'Ketu': (9, 19.0),
    })
    an = analyze_all_grahas(chart)
    m = an['Mercury']
    assert m['degPct'] < 1.0
    assert m['degCapApplied'] is True
    assert abs(m['strengthPct'] - 1.0) < 0.001


def test_degree_cap_does_not_apply_when_deg_pct_is_full():
    """A planet with full degree strength (5-25 deg band) can legitimately
    exceed 100% after boosts — the cap only guards planets that started weak."""
    chart = _chart(2, 15.0, {
        'Sun': (9, 15.0),
        'Venus': (3, 20.0),  # same isolated case as the sun-like-house test
    })
    an = analyze_all_grahas(chart)
    v = an['Venus']
    assert v['degPct'] == 1.0
    assert v['degCapApplied'] is False
    assert v['strengthPct'] > 1.0


# ─── Direct FM-affliction loss keyed to strength, not special/chain ────

def test_strong_planet_single_regular_affliction_loses_exactly_half():
    """A strong planet (>=70% pre-affliction) hit by one regular (non-special)
    FM within its 1deg damage orb loses exactly 50% flat -- this is the
    baseLoss = planetIsStrong ? 0.5 : 0.75 rule; it must not be keyed off
    special/chainSpecial (that bug shipped loss=0.75 for a regular affliction
    on a strong planet, and loss=0.5 for a special one -- backwards).
    Gemini rising (lr=3, no regular FM for this ascendant) keeps Mercury
    itself a non-FM target; Rahu's 7th aspect from house1 reaches house7
    (Mercury), and the ascendant degree (25) is kept far from both so the
    house-MEP mechanisms stay silent -- isolates the direct-affliction path."""
    chart = _chart(3, 25.0, {
        'Mercury': (9, 10.5),   # house7
        'Rahu': (3, 10.3),      # house1, 7th aspect -> house7, orb ~0.2
    })
    an = analyze_all_grahas(chart)
    m = an['Mercury']
    assert m['planetIsStrong'] is True
    assert len(m['afflictions']) == 1
    assert m['afflictions'][0]['special'] is False
    assert abs(m['strengthPct'] - 0.5) < 0.001


def test_cond5_flat_quarter_strength():
    """2+ distinct FMs within 5 deg of a planet -> flat 25% remaining strength.
    Taurus rising: Mars and Venus (both FM) conjunct Mercury in house1
    (not a sun-like house, so no boost dilutes the check)."""
    chart = _chart(2, 25.0, {
        'Mercury': (2, 10.5),
        'Mars':    (2, 10.2),
        'Venus':   (2, 10.8),
    })
    an = analyze_all_grahas(chart)
    m = an['Mercury']
    assert m['cond5'] is True
    assert abs(m['strengthPct'] - 0.25) < 0.001


# ─── FM self-affliction of its own occupied house ──────────────────────

def test_fm_can_afflict_own_occupied_house_unless_own_mt_sign():
    """A functional malefic sitting in a house that is NOT its own
    Moolatrikona sign, close to that house's MEP, weakens itself exactly
    like it would weaken any other planet there — real user-reported case
    (Taurus rising: Jupiter and Saturn both in house1/Taurus)."""
    chart = _chart(2, 15 + 46/60, {
        'Sun': (5, 10.0), 'Moon': (8, 10.0), 'Mars': (9, 10.0),
        'Mercury': (5, 10.0), 'Jupiter': (2, 15 + 56/60),
        'Venus': (9, 10.0), 'Saturn': (2, 5 + 57/60),
        'Rahu': (5, 10.0), 'Ketu': (11, 10.0),
    })
    an = analyze_all_grahas(chart)
    assert abs(an['Saturn']['strengthPct'] - 0.275) < 0.001
    assert abs(an['Jupiter']['strengthPct'] - 0.275) < 0.001


# ─── Rule 5d ────────────────────────────────────────────────────────────

def test_rule5d_point1_gated_by_cfg():
    """FM within orb of the Lagna Lord's own degree fails only when
    cfg.noFmLagna is true; the identical chart passes with it off. Minimal
    cfg (not the full IDEAL_CFG) so only Rule 5d is under test -- IDEAL_CFG's
    other minimums (lagnaLordMin, minStrongPlanets, antarMin, ...) aren't
    satisfiable by a 2-planet synthetic chart and aren't what this pins."""
    lr = 2
    chart = _chart(lr, 15.0, {
        'Moon': (lr, 15.0),   # house1, lagna lord for Taurus rising
        'Mars': (lr, 18.0),   # conjunct, FM for Taurus, orb=3 -- regular, non-damaging
    })
    an = analyze_all_grahas(chart)
    assert an['Moon']['allFmAspects'], "expected a regular (non-damaging) affliction on Moon"

    cfg_base = {'lagnaLordMin': 0, 'planetMins': {}}
    result_on = screen_muhurta(chart, an, {**cfg_base, 'noFmLagna': True})
    assert result_on['pass'] is False
    assert 'Lagna Lord' in result_on['reason']

    result_off = screen_muhurta(chart, an, {**cfg_base, 'noFmLagna': False})
    assert result_off['pass'] is True


def test_rule5d_absent_when_no_fm_lagna_flag():
    """Baseline: an uncontested chart passes cleanly regardless of noFmLagna."""
    lr = 2
    chart = _chart(lr, 15.0, {'Moon': (lr, 15.0)})
    an = analyze_all_grahas(chart)
    cfg_base = {'lagnaLordMin': 0, 'planetMins': {}, 'minStrongPlanets': 0, 'minStrongHouses': 0}
    result = screen_muhurta(chart, an, {**cfg_base, 'noFmLagna': False})
    assert result['pass'] is True


# ─── Golden-value regression (pinned from a real chart, 2026-07-17) ────
# Source: POST /api/v1/chart {date:1990-05-15, time:14:30:00, lat:28.6139,
# lon:77.2090, tz:5.5, include_analysis:true} against the live server.

GOLDEN_CHART = {
    'lagna': {'rashi': 6, 'degree_in_rashi': 1.8982},
    'grahas': [
        {'graha': 'Sun', 'rashi': 2, 'degree_in_rashi': 0.5434, 'retrograde': False},
        {'graha': 'Moon', 'rashi': 10, 'degree_in_rashi': 1.8872, 'retrograde': False},
        {'graha': 'Mars', 'rashi': 11, 'degree_in_rashi': 24.5088, 'retrograde': False},
        {'graha': 'Mercury', 'rashi': 1, 'degree_in_rashi': 14.2959, 'retrograde': False},
        {'graha': 'Jupiter', 'rashi': 3, 'degree_in_rashi': 15.7859, 'retrograde': False},
        {'graha': 'Venus', 'rashi': 12, 'degree_in_rashi': 18.9436, 'retrograde': False},
        {'graha': 'Saturn', 'rashi': 10, 'degree_in_rashi': 1.5193, 'retrograde': False},
        {'graha': 'Rahu', 'rashi': 10, 'degree_in_rashi': 16.5236, 'retrograde': False},
        {'graha': 'Ketu', 'rashi': 4, 'degree_in_rashi': 16.5236, 'retrograde': False},
    ],
    'birth_data': {'date': '1990-05-15', 'time': '14:30:00'},
    'dasha': [],
}

GOLDEN_STRENGTH = {
    'Sun': 0.08633, 'Moon': 0.01549, 'Mars': 0.176357, 'Mercury': 0.176357,
    'Jupiter': 1.0, 'Venus': 0.210113, 'Saturn': 0.176357,
    'Rahu': 0.661515, 'Ketu': 0.01549,
}


def test_golden_chart_strength_regression():
    an = analyze_all_grahas(GOLDEN_CHART)
    for name, expected in GOLDEN_STRENGTH.items():
        assert abs(an[name]['strengthPct'] - expected) < 0.001, (
            f"{name}: got {an[name]['strengthPct']}, expected {expected}"
        )
