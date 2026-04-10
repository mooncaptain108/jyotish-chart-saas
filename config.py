"""Global configuration for the Vedic Jyotish Chart API."""

import swisseph as swe

# Ayanamsa: Lahiri (Chitrapaksha) — standard in Indian Jyotish
AYANAMSA = swe.SIDM_LAHIRI

# House system: Equal ('E') is default; Sripati ('B') available as option
DEFAULT_HOUSE_SYSTEM = b"E"
SRIPATI_HOUSE_SYSTEM = b"B"

# Ephemeris flags
SIDEREAL_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH

# Node type: Mean node for Rahu (traditional Jyotish standard)
RAHU_BODY = swe.TRUE_NODE


EPHE_PATH = '/home/mooncaptain/jyotish-chart-saas/ephemeris'


def init_swisseph():
    """Initialize Swiss Ephemeris with Lahiri ayanamsa and local data files."""
    swe.set_ephe_path(EPHE_PATH)
    swe.set_sid_mode(AYANAMSA)
