"""27 Nakshatras and pada calculation."""

# Each nakshatra spans 13°20' (13.3333°)
NAKSHATRA_SPAN = 13.333333333333334  # 360 / 27

# Each pada spans 3°20' (3.3333°)
PADA_SPAN = 3.333333333333333  # 360 / 108

NAKSHATRA_NAMES = {
    1: "Ashwini",
    2: "Bharani",
    3: "Krittika",
    4: "Rohini",
    5: "Mrigashira",
    6: "Ardra",
    7: "Punarvasu",
    8: "Pushya",
    9: "Ashlesha",
    10: "Magha",
    11: "Purva Phalguni",
    12: "Uttara Phalguni",
    13: "Hasta",
    14: "Chitra",
    15: "Swati",
    16: "Vishakha",
    17: "Anuradha",
    18: "Jyeshtha",
    19: "Moola",
    20: "Purva Ashadha",
    21: "Uttara Ashadha",
    22: "Shravana",
    23: "Dhanishtha",
    24: "Shatabhisha",
    25: "Purva Bhadrapada",
    26: "Uttara Bhadrapada",
    27: "Revati",
}

# Nakshatra lords for Vimshottari Dasha
NAKSHATRA_LORDS = {
    1: "Ketu",       # Ashwini
    2: "Venus",      # Bharani
    3: "Sun",        # Krittika
    4: "Moon",       # Rohini
    5: "Mars",       # Mrigashira
    6: "Rahu",       # Ardra
    7: "Jupiter",    # Punarvasu
    8: "Saturn",     # Pushya
    9: "Mercury",    # Ashlesha
    10: "Ketu",      # Magha
    11: "Venus",     # Purva Phalguni
    12: "Sun",       # Uttara Phalguni
    13: "Moon",      # Hasta
    14: "Mars",      # Chitra
    15: "Rahu",      # Swati
    16: "Jupiter",   # Vishakha
    17: "Saturn",    # Anuradha
    18: "Mercury",   # Jyeshtha
    19: "Ketu",      # Moola
    20: "Venus",     # Purva Ashadha
    21: "Sun",       # Uttara Ashadha
    22: "Moon",      # Shravana
    23: "Mars",      # Dhanishtha
    24: "Rahu",      # Shatabhisha
    25: "Jupiter",   # Purva Bhadrapada
    26: "Saturn",    # Uttara Bhadrapada
    27: "Mercury",   # Revati
}


# Naming syllable (akshara) for each of the 108 padas, per the traditional
# Nama-Nakshatra table used for Vedic baby-naming (Namakaran).
PADA_SYLLABLES = {
    1: ["Chu", "Che", "Cho", "Laa"],       # Ashwini
    2: ["Lee", "Loo", "Le", "Lo"],         # Bharani
    3: ["A", "Ee", "U", "E"],              # Krittika
    4: ["O", "Vaa", "Vee", "Vu"],          # Rohini
    5: ["Ve", "Vo", "Kaa", "Kee"],         # Mrigashira
    6: ["Ku", "Gha", "Ing", "Chha"],       # Ardra
    7: ["Ke", "Ko", "Haa", "Hee"],         # Punarvasu
    8: ["Hu", "He", "Ho", "Daa"],          # Pushya
    9: ["Dee", "Doo", "De", "Do"],         # Ashlesha
    10: ["Maa", "Mee", "Moo", "Me"],       # Magha
    11: ["Mo", "Taa", "Tee", "Too"],       # Purva Phalguni
    12: ["Te", "To", "Paa", "Pee"],        # Uttara Phalguni
    13: ["Poo", "Sha", "Na", "Tha"],       # Hasta
    14: ["Pe", "Po", "Raa", "Ree"],        # Chitra
    15: ["Roo", "Re", "Ro", "Taa"],        # Swati
    16: ["Tee", "Too", "Te", "To"],        # Vishakha
    17: ["Naa", "Nee", "Noo", "Ne"],       # Anuradha
    18: ["No", "Yaa", "Yee", "Yoo"],       # Jyeshtha
    19: ["Ye", "Yo", "Bhaa", "Bhee"],      # Moola
    20: ["Bhoo", "Dhaa", "Phaa", "Dha"],   # Purva Ashadha
    21: ["Bhe", "Bho", "Jaa", "Jee"],      # Uttara Ashadha
    22: ["Khee", "Khoo", "Khe", "Kho"],    # Shravana
    23: ["Gaa", "Gee", "Gu", "Ge"],        # Dhanishtha
    24: ["Go", "Saa", "See", "Soo"],       # Shatabhisha
    25: ["Se", "So", "Daa", "Dee"],        # Purva Bhadrapada
    26: ["Doo", "Tha", "Jha", "Yna"],      # Uttara Bhadrapada
    27: ["De", "Do", "Cha", "Chee"],       # Revati
}


def longitude_to_nakshatra(longitude: float) -> int:
    """Convert sidereal longitude (0–360) to nakshatra number (1–27)."""
    return int(longitude / NAKSHATRA_SPAN) % 27 + 1


def longitude_to_pada(longitude: float) -> int:
    """Convert sidereal longitude (0–360) to pada (1–4) within its nakshatra."""
    nak_start = (longitude_to_nakshatra(longitude) - 1) * NAKSHATRA_SPAN
    offset = longitude - nak_start
    return int(offset / PADA_SPAN) % 4 + 1


def longitude_to_pada_syllable(longitude: float) -> str:
    """Naming syllable for the pada (1 of 4) at this sidereal longitude."""
    nakshatra = longitude_to_nakshatra(longitude)
    pada = longitude_to_pada(longitude)
    return PADA_SYLLABLES[nakshatra][pada - 1]


def nakshatra_traversed_fraction(longitude: float) -> float:
    """Fraction of the current nakshatra already traversed (0.0–1.0)."""
    nak_start = (longitude_to_nakshatra(longitude) - 1) * NAKSHATRA_SPAN
    offset = longitude - nak_start
    return offset / NAKSHATRA_SPAN
