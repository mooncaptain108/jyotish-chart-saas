"""Tests for divisional chart calculations."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculations.divisional import (
    compute_divisional_chart, compute_all_divisional_charts,
    _d1_sign, _d2_sign, _d9_sign,
    _d4_sign, _d16_sign, _d20_sign, _d24_sign, _d27_sign, _d40_sign, _d45_sign,
)
from calculations.ephemeris import datetime_to_jd, compute_all_planets, compute_houses


def test_d1_same_as_rashi():
    """D1 sign should match the rashi from longitude."""
    assert _d1_sign(45.0) == 2    # 45° → Taurus
    assert _d1_sign(0.0) == 1     # 0° → Aries
    assert _d1_sign(359.0) == 12  # 359° → Pisces


def test_d2_hora():
    """D2 (Hora) basic checks."""
    # Aries (odd sign, rashi=1): 0–15° → Leo(5), 15–30° → Cancer(4)
    assert _d2_sign(10.0) == 5   # Aries, first half → Leo
    assert _d2_sign(20.0) == 4   # Aries, second half → Cancer

    # Taurus (even sign, rashi=2): 0–15° → Cancer(4), 15–30° → Leo(5)
    assert _d2_sign(40.0) == 4   # Taurus, first half → Cancer
    assert _d2_sign(55.0) == 5   # Taurus, second half → Leo


def test_d9_navamsa():
    """D9 (Navamsa) basic checks."""
    # 0° Aries (fire sign, start=Aries): part 0 → Aries (1)
    assert _d9_sign(0.0) == 1

    # ~3.5° Aries: part 1 → Taurus (2)
    assert _d9_sign(3.5) == 2


def test_d4_chaturthamsa():
    """D4 (Chaturthamsa) — uniform kendra (1-4-7-10) rule from the sign."""
    assert _d4_sign(0.0) == 1     # Aries, part0 -> Aries (same sign)
    assert _d4_sign(10.0) == 4    # Aries, part1 (7.5-15) -> Cancer (4th)
    assert _d4_sign(20.0) == 7    # Aries, part2 (15-22.5) -> Libra (7th)
    assert _d4_sign(25.0) == 10   # Aries, part3 (22.5-30) -> Capricorn (10th)


def test_d16_shodasamsa():
    """D16 — movable/fixed/dual start from Aries/Leo/Sagittarius."""
    assert _d16_sign(0.0) == 1     # Aries (movable) -> Aries
    assert _d16_sign(30.0) == 5    # Taurus (fixed) -> Leo
    assert _d16_sign(60.0) == 9    # Gemini (dual) -> Sagittarius


def test_d20_vimsamsa():
    """D20 — movable/fixed/dual start from Aries/Sagittarius/Leo."""
    assert _d20_sign(0.0) == 1     # Aries (movable) -> Aries
    assert _d20_sign(30.0) == 9    # Taurus (fixed) -> Sagittarius
    assert _d20_sign(60.0) == 5    # Gemini (dual) -> Leo


def test_d24_chaturvimsamsa():
    """D24 — odd signs start from Leo, even signs from Cancer."""
    assert _d24_sign(0.0) == 5     # Aries (odd) -> Leo
    assert _d24_sign(30.0) == 4    # Taurus (even) -> Cancer


def test_d27_saptavimsamsa():
    """D27 — fire/earth/air/water start from Aries/Cancer/Libra/Capricorn."""
    assert _d27_sign(0.0) == 1     # Aries (fire) -> Aries
    assert _d27_sign(30.0) == 4    # Taurus (earth) -> Cancer
    assert _d27_sign(60.0) == 7    # Gemini (air) -> Libra
    assert _d27_sign(90.0) == 10   # Cancer (water) -> Capricorn


def test_d40_khavedamsa():
    """D40 — odd signs start from Aries, even signs from Libra."""
    assert _d40_sign(0.0) == 1     # Aries (odd) -> Aries
    assert _d40_sign(30.0) == 7    # Taurus (even) -> Libra


def test_d45_akshavedamsa():
    """D45 — movable/fixed/dual start from Aries/Leo/Sagittarius."""
    assert _d45_sign(0.0) == 1     # Aries (movable) -> Aries
    assert _d45_sign(30.0) == 5    # Taurus (fixed) -> Leo
    assert _d45_sign(60.0) == 9    # Gemini (dual) -> Sagittarius


def test_all_divisional_charts():
    """All 16 divisional charts (full shodasavarga) should be computed."""
    jd = datetime_to_jd(1990, 5, 15, 9.0)
    positions = compute_all_planets(jd)
    cusps, ascmc = compute_houses(jd, 28.6139, 77.2090)

    charts = compute_all_divisional_charts(positions, ascmc[0])
    assert len(charts) == 16

    chart_types = [c["chart_type"] for c in charts]
    for ct in ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
               "D20", "D24", "D27", "D30", "D40", "D45", "D60"]:
        assert ct in chart_types


def test_divisional_chart_structure():
    """Each divisional chart should have lagna and 9 grahas."""
    jd = datetime_to_jd(1990, 5, 15, 9.0)
    positions = compute_all_planets(jd)
    cusps, ascmc = compute_houses(jd, 28.6139, 77.2090)

    chart = compute_divisional_chart(positions, ascmc[0], "D9")
    assert "lagna" in chart
    assert "grahas" in chart
    assert len(chart["grahas"]) == 9
    assert 1 <= chart["lagna"]["rashi"] <= 12
