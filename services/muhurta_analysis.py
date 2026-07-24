"""
Port of JS analyzeAllGrahas() and screenMuhurta() from client-side.
Produces identical strengthPct values to the JS implementation.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any

# ─── Jyotish constants ─────────────────────────────────────────────────────

DEBI_RASHI  = {'Sun':7,'Moon':8,'Mars':4,'Mercury':12,'Jupiter':10,'Venus':6,'Saturn':1,'Rahu':8,'Ketu':2}
EXALT_RASHI = {'Sun':1,'Moon':2,'Mars':10,'Mercury':6,'Jupiter':4,'Venus':12,'Saturn':7,'Rahu':2,'Ketu':8}
MOOLA_RASHI = {'Sun':5,'Moon':4,'Mars':1,'Mercury':6,'Jupiter':9,'Venus':7,'Saturn':11}
MOOLA_LORD  = {1:'Mars',4:'Moon',5:'Sun',6:'Mercury',7:'Venus',9:'Jupiter',11:'Saturn'}
RASHI_NAME  = ['','Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra',
               'Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

FUNC_MALEFICS: dict[int, set[str]] = {
    1: {'Mercury'},
    2: {'Mars','Venus','Jupiter'},
    3: set(),
    4: {'Jupiter','Saturn'},
    5: {'Moon'},
    6: {'Sun','Saturn','Mars'},
    7: {'Mercury'},
    8: {'Venus','Mars'},
    9: {'Moon'},
    10: {'Sun','Jupiter'},
    11: {'Moon','Mercury'},
    12: {'Sun','Venus','Saturn'},
}

MMP = {1:'Ketu',2:'Jupiter',3:'Ketu',4:'Saturn',5:'Moon',6:'Mars',
       7:'Mercury',8:'Venus',9:'Moon',10:'Sun',11:'Mercury',12:'Venus'}

COMBUST_ORB    = {'Moon':12,'Mars':17,'Mercury':14,'Jupiter':11,'Venus':10,'Saturn':16}
ASPECT_OFFSETS = {'default':[6],'Mars':[6,3,7],'Jupiter':[6,4,8],
                  'Saturn':[6,2,9],'Rahu':[6,4,8],'Ketu':[6,4,8]}
DUSHTANA       = {6, 8, 12}

MUHURTA_PLANETS = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']
LAGNA_RULER     = {1:'Mars',2:'Moon',3:'Sun',4:'Moon',5:'Sun',6:'Mercury',
                   7:'Venus',8:'Jupiter',9:'Jupiter',10:'Saturn',11:'Saturn',12:'Mars'}
NAK_LORDS_27    = [
    'Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury',
    'Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury',
    'Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury',
]

# Canonical "Ideal" muhurta screening config — single source of truth (was
# previously duplicated as a JS-only object literal in static/index.html).
IDEAL_CFG: dict = {
    'minBeneficDays': 30, 'antarMin': 0.70, 'lagnaLordMin': 0.70,
    'minStrongPlanets': 4, 'minStrongHouses': 7, 'mepOrb': 5,
    'planetMins': {}, 'allowWeakAntar': False, 'lowerStrongThreshold': False,
    'noFmLagna': True,
}

# ─── Helpers ───────────────────────────────────────────────────────────────

def fm_aspected_houses(graha: str, from_house: int) -> set[int]:
    houses = {from_house}
    for off in ASPECT_OFFSETS.get(graha, ASPECT_OFFSETS['default']):
        houses.add(((from_house - 1 + off) % 12) + 1)
    return houses


def abs_diff_deg(rashi_a: int, deg_a: float, rashi_b: int, deg_b: float) -> float:
    """Circular distance in degrees between two (rashi 1-12, degree 0-30) points,
    so a planet at rashi 2 ~29.97 deg reads as ~0.4 deg from rashi 3 ~0.37 deg
    instead of the bogus ~29.6 deg a same-rashi subtraction would give."""
    a = (rashi_a - 1) * 30 + deg_a
    b = (rashi_b - 1) * 30 + deg_b
    d = abs(a - b)
    return min(d, 360.0 - d)


def mep_rashi(lagna_rashi: int, house: int) -> int:
    """The rashi (1-12) that house N's MEP (ascendant degree replicated into
    house N) falls in."""
    return ((lagna_rashi - 1 + (house - 1)) % 12) + 1


def mep_orb(graha: str, from_house: int, deg: float, rashi: int,
            target_house: int, mep_deg: float, lagna_rashi: int) -> float:
    """Effective orb between a planet and target_house's MEP: the smaller of
    (a) its aspect-projected degree distance if it classically aspects
    target_house (drishti preserves degree-in-sign across the projection,
    so no rashi is involved), and (b) its raw circular distance to the
    MEP's absolute position (only ever small for conjunction or physical
    boundary adjacency, independent of classical drishti)."""
    candidates = [abs_diff_deg(rashi, deg, mep_rashi(lagna_rashi, target_house), mep_deg)]
    if target_house in fm_aspected_houses(graha, from_house):
        candidates.append(abs(deg - mep_deg))
    return min(candidates)


def aspect_label(graha: str, from_house: int, to_house: int) -> str:
    if from_house == to_house:
        return 'conjunct'
    for off in ASPECT_OFFSETS.get(graha, ASPECT_OFFSETS['default']):
        if ((from_house - 1 + off) % 12) + 1 == to_house:
            n = off + 1
            if n == 2: return '2nd aspect'
            if n == 3: return '3rd aspect'
            if n == 4: return '4th aspect'
            return f'{n}th aspect'
    return 'aspect'


def is_strong(deg: float) -> bool:
    return 5.0 <= deg <= 25.0


def deg_strength(deg: float) -> float:
    if 5.0 <= deg <= 25.0:
        return 1.0
    if deg < 5.0:
        return deg / 5.0
    return (30.0 - deg) / 5.0


# ─── analyze_all_grahas ────────────────────────────────────────────────────

def analyze_all_grahas(data: dict) -> dict[str, Any]:
    """Exact port of JS analyzeAllGrahas(data). Returns analysis dict."""
    lr       = data['lagna']['rashi']
    fms      = FUNC_MALEFICS.get(lr, set())
    sun_is_fm = 'Sun' in fms
    mmp      = MMP.get(lr)
    mep_deg  = data['lagna']['degree_in_rashi']

    # D9 rashi lookup
    d9_rashi: dict[str, int] = {}
    d9_lagna  = None
    for dc in (data.get('divisional_charts') or []):
        if dc.get('chart_type') == 'D9':
            for g in (dc.get('grahas') or []):
                d9_rashi[g['graha']] = g['rashi']
            if dc.get('lagna'):
                d9_lagna = dc['lagna']['rashi']
            break

    # Sun-like planets: lords of 2nd, 3rd, 9th houses that contain a mooltrikona sign
    sun_like_signs = {5}
    sun_like_planets: set[str] = set()
    for h in [2, 3, 9]:
        hr = ((lr - 1 + h - 1) % 12) + 1
        lord = MOOLA_LORD.get(hr)
        if lord:
            sun_like_signs.add(hr)
            sun_like_planets.add(lord)

    # Combustion
    sun_g   = next((g for g in data['grahas'] if g['graha'] == 'Sun'), None)
    sun_lon = ((sun_g['rashi'] - 1) * 30 + sun_g['degree_in_rashi']) if sun_g else None
    combust_set: set[str] = set()
    if sun_lon is not None:
        for g in data['grahas']:
            orb = COMBUST_ORB.get(g['graha'])
            if not orb:
                continue
            lon = (g['rashi'] - 1) * 30 + g['degree_in_rashi']
            d = abs(lon - sun_lon)
            if d > 180:
                d = 360 - d
            if d <= orb:
                combust_set.add(g['graha'])

    # FM list
    fm_data = []
    for g in data['grahas']:
        if g['graha'] in ('Rahu', 'Ketu') or g['graha'] in fms:
            house = ((g['rashi'] - lr + 12) % 12) + 1
            fm_data.append({'graha': g['graha'], 'house': house,
                            'deg': g['degree_in_rashi'], 'rashi': g['rashi']})

    # Chain-special FMs
    chain_special: dict[str, str] = {}
    for fm in fm_data:
        for src in fm_data:
            if src['graha'] == fm['graha']:
                continue
            src_is_node = src['graha'] in ('Rahu', 'Ketu')
            if fm['house'] not in fm_aspected_houses(src['graha'], src['house']):
                continue
            if src_is_node and src['house'] != fm['house']:
                continue
            if abs(src['deg'] - fm['deg']) <= 5:
                chain_special[fm['graha']] = src['graha']
                break

    # ── First pass: per-planet base analysis ──
    analysis: dict[str, Any] = {}
    for g in data['grahas']:
        name    = g['graha']
        is_node = name in ('Rahu', 'Ketu')
        house   = ((g['rashi'] - lr + 12) % 12) + 1
        is_fm   = is_node or name in fms
        is_mmp  = name == mmp
        combust = name in combust_set

        deg_pct      = 1.0 if is_node else deg_strength(g['degree_in_rashi'])
        weak_by_deg  = not is_node and not is_strong(g['degree_in_rashi'])
        debilitated  = DEBI_RASHI.get(name) == g['rashi']
        d9_debi      = (name in d9_rashi and DEBI_RASHI.get(name) == d9_rashi[name])
        exalted      = EXALT_RASHI.get(name) == g['rashi']
        in_own_mt    = not is_node and MOOLA_RASHI.get(name) == g['rashi']
        in_sun_like_house  = not is_node and house in (2, 3, 9)
        in_leo             = not is_node and g['rashi'] == 5 and name != 'Sun'
        is_sun_like_planet = not is_node and name != 'Sun' and name in sun_like_planets
        d9_exalted   = (name in d9_rashi and EXALT_RASHI.get(name) == d9_rashi[name])
        d9_house     = (((d9_rashi[name] - d9_lagna + 12) % 12) + 1
                        if d9_lagna is not None and name in d9_rashi else None)
        d9_in_dust   = d9_house is not None and d9_house in DUSHTANA
        in_dushtana  = house in DUSHTANA and MOOLA_LORD.get(g['rashi']) != name
        dispositor   = MOOLA_LORD.get(g['rashi'])

        # Preliminary strength (for damage-orb calculation)
        prelim = 1.0 if is_node else deg_pct
        if combust:     prelim *= 0.25 if sun_is_fm else 0.5
        if debilitated: prelim *= 0.25 if d9_debi else 0.5
        if in_dushtana: prelim *= 0.4  if (d9_debi and not debilitated) else 0.5
        elif d9_debi and not debilitated: prelim *= 0.75
        planet_is_strong = not is_node and prelim >= 0.70

        # FM aspects to this planet
        afflictions   = []
        all_fm_aspects = []
        for fm in fm_data:
            if fm['graha'] == name:
                continue
            if is_node and fm['graha'] in ('Rahu', 'Ketu'):
                continue
            if house not in fm_aspected_houses(fm['graha'], fm['house']):
                continue
            diff = abs(fm['deg'] - g['degree_in_rashi'])
            if diff >= 5:
                continue
            via        = aspect_label(fm['graha'], fm['house'], house)
            is_node_fm = fm['graha'] in ('Rahu', 'Ketu')
            is_conj    = fm['house'] == house
            fm_in_dust = fm['house'] in DUSHTANA and MOOLA_LORD.get(fm['rashi']) != fm['graha']
            special    = fm['graha'] == mmp or (is_node_fm and is_conj) or fm_in_dust
            c_spec     = fm['graha'] in chain_special
            c_src      = chain_special.get(fm['graha'])
            eff_spec   = special or c_spec
            dmg_orb    = 5 if not planet_is_strong else (2 if eff_spec else 1)
            is_dmg     = diff < dmg_orb
            entry = {'fm': fm['graha'], 'orb': diff, 'special': special,
                     'chainSpecial': c_spec, 'chainSource': c_src,
                     'via': via, 'isDamaging': is_dmg, 'dmgOrb': dmg_orb,
                     'isMmp': fm['graha'] == mmp, 'fmInDust': fm_in_dust}
            all_fm_aspects.append(entry)
            if is_dmg:
                afflictions.append({'fm': fm['graha'], 'orb': diff, 'special': special,
                    'chainSpecial': c_spec, 'chainSource': c_src, 'via': via, 'dmgOrb': dmg_orb})

        # FB aspects
        fb_aspects = []
        for fb in data['grahas']:
            if fb['graha'] in (name, 'Rahu', 'Ketu') or fb['graha'] in fms:
                continue
            fb_house = ((fb['rashi'] - lr + 12) % 12) + 1
            if house not in fm_aspected_houses(fb['graha'], fb_house):
                continue
            orb = abs(fb['degree_in_rashi'] - g['degree_in_rashi'])
            if orb >= 5:
                continue
            fb_aspects.append({'fb': fb['graha'], 'orb': orb,
                               'via': aspect_label(fb['graha'], fb_house, house)})

        # Ra-Ke axis merge for all_fm_aspects / afflictions
        ra_i = next((i for i, a in enumerate(all_fm_aspects) if a['fm'] == 'Rahu'), -1)
        ke_i = next((i for i, a in enumerate(all_fm_aspects) if a['fm'] == 'Ketu'), -1)
        if ra_i >= 0 and ke_i >= 0:
            ra, ke = all_fm_aspects[ra_i], all_fm_aspects[ke_i]
            ax = {
                'fm': 'Ra-Ke', 'isRaKe': True,
                'orb':        min(ra['orb'], ke['orb']),
                'special':    ra['special'] or ke['special'],
                'chainSpecial': ra['chainSpecial'] or ke['chainSpecial'],
                'chainSource':  ra['chainSource'] or ke['chainSource'],
                'via':        ra['via'] if ra['orb'] <= ke['orb'] else ke['via'],
                'dmgOrb':     ra['dmgOrb'] if ra['isDamaging'] else ke['dmgOrb'],
                'isDamaging': ra['isDamaging'] or ke['isDamaging'],
                'isMmp':      ra.get('isMmp') or ke.get('isMmp'),
                'fmInDust':   ra.get('fmInDust') or ke.get('fmInDust'),
            }
            lo, hi = min(ra_i, ke_i), max(ra_i, ke_i)
            del all_fm_aspects[hi]; del all_fm_aspects[lo]
            all_fm_aspects.insert(0, ax)
            afflictions[:] = [a for a in afflictions if a['fm'] not in ('Rahu', 'Ketu')]
            if ax['isDamaging']:
                afflictions.insert(0, {'fm': 'Ra-Ke', 'isRaKe': True, 'orb': ax['orb'],
                    'special': ax['special'], 'chainSpecial': ax['chainSpecial'],
                    'chainSource': ax['chainSource'], 'via': ax['via'], 'dmgOrb': ax['dmgOrb']})

        # Condition 5: 2+ distinct FMs within 5°
        cond5 = len(all_fm_aspects) >= 2
        if cond5:
            for asp in all_fm_aspects:
                asp['special'] = True; asp['cond5'] = True; asp['isDamaging'] = True
            afflictions.clear()
            for asp in all_fm_aspects:
                afflictions.append({'fm': asp['fm'], 'orb': asp['orb'], 'special': True,
                    'chainSpecial': asp['chainSpecial'], 'chainSource': asp['chainSource'],
                    'via': asp['via'], 'dmgOrb': asp.get('dmgOrb'), 'cond5': True,
                    'isRaKe': asp.get('isRaKe')})

        # MT house MEP afflictions
        mt_aff = []
        mt_rashi = MOOLA_RASHI.get(name)
        if mt_rashi:
            mt_house = ((mt_rashi - lr + 12) % 12) + 1
            mt_raw = []
            for fm in fm_data:
                if fm['graha'] == name:
                    continue
                orb = mep_orb(fm['graha'], fm['house'], fm['deg'], fm['rashi'], mt_house, mep_deg, lr)
                if orb >= 5:
                    continue
                is_fn  = fm['graha'] in ('Rahu', 'Ketu')
                is_fc  = fm['house'] == mt_house
                fm_dt  = fm['house'] in DUSHTANA and MOOLA_LORD.get(fm['rashi']) != fm['graha']
                fm_ch  = fm['graha'] in chain_special
                spec   = fm['graha'] == mmp or (is_fn and is_fc) or fm_dt or fm_ch
                mt_raw.append({'fm': fm['graha'], 'orb': orb, 'special': spec,
                               'inMtHouse': is_fc, 'mtHouse': mt_house})
            # Ra-Ke merge
            ra_i = next((i for i, a in enumerate(mt_raw) if a['fm'] == 'Rahu'), -1)
            ke_i = next((i for i, a in enumerate(mt_raw) if a['fm'] == 'Ketu'), -1)
            if ra_i >= 0 and ke_i >= 0:
                re, ke_e = mt_raw[ra_i], mt_raw[ke_i]
                lo, hi = min(ra_i, ke_i), max(ra_i, ke_i)
                del mt_raw[hi]; del mt_raw[lo]
                mt_raw.insert(0, {'fm': 'Ra-Ke', 'orb': min(re['orb'], ke_e['orb']),
                    'special': True, 'inMtHouse': re['inMtHouse'] or ke_e['inMtHouse'],
                    'mtHouse': mt_house, 'isRaKe': True})
            mt_c5 = len(mt_raw) >= 2
            for mta in mt_raw:
                s = mta['special'] or mt_c5
                if s:
                    loss = 0.75 if mta['orb'] < 2 else 0.75 * (1 - (mta['orb'] - 2) / 3)
                else:
                    loss = 0.75 if mta['orb'] < 1 else 0.75 * (1 - (mta['orb'] - 1) / 4)
                mt_aff.append({**mta, 'loss': loss, 'special': s, 'cond5': mt_c5})

        # House of occupation MEP afflictions
        occ_aff = []
        if not is_node and MOOLA_RASHI.get(name) != g['rashi']:
            is_mt = bool(MOOLA_LORD.get(g['rashi']))
            occ_raw = []
            for fm in fm_data:
                orb = mep_orb(fm['graha'], fm['house'], fm['deg'], fm['rashi'], house, mep_deg, lr)
                if orb >= 5:
                    continue
                is_fn2 = fm['graha'] in ('Rahu', 'Ketu')
                is_fc2 = fm['house'] == house
                fm_dt2 = fm['house'] in DUSHTANA and MOOLA_LORD.get(fm['rashi']) != fm['graha']
                fm_ch2 = fm['graha'] in chain_special
                spec2  = fm['graha'] == mmp or (is_fn2 and is_fc2) or fm_dt2 or fm_ch2
                occ_raw.append({'fm': fm['graha'], 'orb': orb, 'special': spec2, 'isMtSign': is_mt})
            # Ra-Ke merge
            ra_i = next((i for i, a in enumerate(occ_raw) if a['fm'] == 'Rahu'), -1)
            ke_i = next((i for i, a in enumerate(occ_raw) if a['fm'] == 'Ketu'), -1)
            if ra_i >= 0 and ke_i >= 0:
                re, ke_e = occ_raw[ra_i], occ_raw[ke_i]
                lo, hi = min(ra_i, ke_i), max(ra_i, ke_i)
                del occ_raw[hi]; del occ_raw[lo]
                occ_raw.insert(0, {'fm': 'Ra-Ke', 'orb': min(re['orb'], ke_e['orb']),
                    'special': True, 'isMtSign': is_mt, 'isRaKe': True})
            occ_c5 = len(occ_raw) >= 2
            for oa in occ_raw:
                s = oa['special'] or occ_c5
                if is_mt:
                    if s:
                        loss = 0.75 if oa['orb'] < 2 else 0.75 * (1 - (oa['orb'] - 2) / 3)
                    else:
                        loss = 0.75 if oa['orb'] < 1 else 0.75 * (1 - (oa['orb'] - 1) / 4)
                else:
                    loss = (0.75 if s else 0.5) * (1 - oa['orb'] / 5)
                occ_aff.append({**oa, 'loss': loss, 'special': s, 'cond5': occ_c5})

        base_weak = (weak_by_deg or combust or debilitated or in_dushtana or cond5
                     or bool(afflictions) or bool(mt_aff) or bool(occ_aff))

        # Strength pipeline: states → MT house MEP → occ house MEP → direct FM
        sp = 1.0 if is_node else deg_pct
        if not is_node:
            if combust:     sp *= 0.25 if sun_is_fm else 0.5
            if debilitated: sp *= 0.25 if d9_debi else 0.5
            if in_dushtana: sp *= 0.4  if (d9_debi and not debilitated) else 0.5
            elif d9_debi and not debilitated: sp *= 0.75
        for mta in mt_aff:
            sp *= (1 - mta['loss'])
        for oa in occ_aff:
            sp *= (1 - oa['loss'])
        if not is_node:
            if cond5:
                sp *= 0.25
            else:
                for aff in afflictions:
                    base_loss = 0.5 if planet_is_strong else 0.75
                    if planet_is_strong:
                        sp *= (1 - base_loss)
                    else:
                        sp *= (1 - base_loss * (1 - aff['orb'] / 5))

        # Positive boosts
        if not is_node and exalted:    sp *= 1.25
        # Sun-like boosts — all three stack independently; suppressed only when
        # the planet is itself a functional malefic AND any FM is within 1° of
        # its occupied house MEP (only a malefic's own boost is suppressible
        # this way — benefics are never suppressed), except an FM in its own MT
        # sign keeps all boosts regardless.
        if not is_fm:
            mep_house_afflicted = False
        elif in_own_mt:
            mep_house_afflicted = False
        else:
            mep_house_afflicted = any(a['orb'] < 1 for a in occ_aff)
        sun_like_boost = False
        if is_sun_like_planet:                          sp *= 1.25; sun_like_boost = True
        if in_own_mt        and not mep_house_afflicted: sp *= 1.25; sun_like_boost = True
        if in_sun_like_house and not mep_house_afflicted: sp *= 1.25; sun_like_boost = True
        if in_leo           and not mep_house_afflicted: sp *= 1.25; sun_like_boost = True
        if d9_exalted and not d9_in_dust: sp *= 1.25

        analysis[name] = {
            'graha': name, 'rashi': g['rashi'],
            'house': house, 'deg': g['degree_in_rashi'], 'retro': g.get('retrograde', False),
            'isFM': is_fm, 'isMMP': is_mmp, 'isNode': is_node,
            'combust': combust, 'weakByDeg': weak_by_deg,
            'debilitated': debilitated, 'd9Debilitated': d9_debi,
            'exalted': exalted, 'inOwnMT': in_own_mt,
            'd9Exalted': d9_exalted, 'd9House': d9_house, 'd9InDushtana': d9_in_dust,
            'inDushtana': in_dushtana,
            'afflictions': afflictions, 'allFmAspects': all_fm_aspects,
            'mtAfflictions': mt_aff, 'occAfflictions': occ_aff,
            'cond5': cond5, 'dispositor': dispositor,
            'degPct': deg_pct, 'strengthPct': sp,
            'planetIsStrong': planet_is_strong, 'sunLikeBoost': sun_like_boost,
            'isSunLikePlanet': is_sun_like_planet, 'inSunLikeHouse': in_sun_like_house,
            'inLeo': in_leo, 'mepHouseAfflicted': mep_house_afflicted,
            'fbAspects': fb_aspects, 'fbBoostItems': [],
            'baseWeak': base_weak, 'dispositorWeak': False,
            'isWeak': base_weak, 'dispCapChain': [], 'degCapApplied': False,
        }

    # ── FB boost pass (snapshot pre-boost so order doesn't matter) ──
    pre_boost = {n: a['strengthPct'] for n, a in analysis.items()
                 if isinstance(a, dict) and 'graha' in a}
    for a in list(analysis.values()):
        if not isinstance(a, dict) or 'graha' not in a or a['isNode']:
            continue
        for fba in a['fbAspects']:
            fb_str = pre_boost.get(fba['fb'])
            if fb_str is None:
                continue
            fb_strong = fb_str >= 0.70
            boost = 0.0
            if fb_strong:
                if fba['orb'] <= 5: boost = 0.5 * (1 - fba['orb'] / 5)
            else:
                if fba['orb'] < 1:  boost = 0.125 * (1 - fba['orb'])
            if boost <= 0:
                continue
            a['strengthPct'] *= (1 + boost)
            a['fbBoostItems'].append({'fb': fba['fb'], 'orb': fba['orb'],
                'via': fba['via'], 'boost': boost, 'fbStrong': fb_strong})

    # ── Dispositor cap cascade (max 7 passes) ──
    for _ in range(7):
        changed = False
        for a in analysis.values():
            if not isinstance(a, dict) or 'graha' not in a:
                continue
            if not a['dispositor'] or a['dispositor'] == a['graha']:
                continue
            disp = analysis.get(a['dispositor'])
            if not isinstance(disp, dict):
                continue
            if disp['isWeak']:
                if not a['dispositorWeak']:
                    a['dispositorWeak'] = True; a['isWeak'] = True; changed = True
                cap = disp['strengthPct']
                if cap < a['strengthPct']:
                    a['strengthPct'] = cap
                    a['dispCapChain'] = [a['dispositor']] + disp['dispCapChain']
                    changed = True
        if not changed:
            break

    # ── Update isWeak from final strengthPct ──
    for a in analysis.values():
        if isinstance(a, dict) and 'graha' in a and a['strengthPct'] >= 0.60:
            a['isWeak'] = False

    # ── Degree cap — planet that started below 100% (old age or infancy) cannot exceed 100% ──
    for a in analysis.values():
        if isinstance(a, dict) and 'graha' in a and not a['isNode'] and a['degPct'] < 1.0 and a['strengthPct'] > 1.0:
            a['strengthPct'] = 1.0
            a['degCapApplied'] = True

    # ── House strengths ──
    houses: dict[int, dict] = {}
    for h in range(1, 13):
        hr = ((lr - 1 + h - 1) % 12) + 1
        mt_lord = MOOLA_LORD.get(hr)
        if mt_lord:
            houses[h] = {'mt': True, 'rashi': hr, 'lord': mt_lord}
        else:
            sp = 1.0
            boosts_h = []; aff_h = []
            # FB boosts to house
            for g in data['grahas']:
                if g['graha'] in ('Rahu', 'Ketu') or g['graha'] in fms:
                    continue
                gh  = ((g['rashi'] - lr + 12) % 12) + 1
                orb = mep_orb(g['graha'], gh, g['degree_in_rashi'], g['rashi'], h, mep_deg, lr)
                an  = analysis.get(g['graha'])
                ps  = isinstance(an, dict) and an.get('strengthPct', 0) >= 0.70
                boost = 0.0
                if ps:
                    if orb <= 5: boost = 0.5 * (1 - orb / 5)
                else:
                    if orb < 1:  boost = 0.125 * (1 - orb)
                if boost > 0:
                    sp += boost
                    boosts_h.append({'planet': g['graha'], 'orb': orb, 'boost': boost})
            # FM afflictions to house (nodes special only when conjunct; a
            # pure 5th/9th aspect is regular)
            for fm in fm_data:
                orb = mep_orb(fm['graha'], fm['house'], fm['deg'], fm['rashi'], h, mep_deg, lr)
                if orb >= 5:
                    continue
                is_fm_conj = fm['house'] == h
                is_fm_node = fm['graha'] in ('Rahu', 'Ketu')
                is_sp = fm['graha'] == mmp or (is_fm_node and is_fm_conj)
                loss  = (0.75 if is_sp else 0.5) * (1 - orb / 5)
                if loss <= 0:
                    continue
                sp -= loss
                aff_h.append({'planet': fm['graha'], 'orb': orb, 'loss': loss,
                              'isSpecial': is_sp, 'isFMconj': is_fm_conj})
            # Ra-Ke axis: single consolidated loss (special only if one node is conjunct)
            only_nodes = bool(aff_h) and all(a['planet'] in ('Rahu', 'Ketu') for a in aff_h)
            rk_loss = None
            if only_nodes:
                for a in aff_h: sp += a['loss']
                rk_orb = min(a['orb'] for a in aff_h)
                rk_special = any(a['isFMconj'] for a in aff_h)
                rk_loss = (0.75 if rk_special else 0.5) * (1 - rk_orb / 5)
                sp -= rk_loss
            sp = max(sp, 0.0)
            houses[h] = {'mt': False, 'rashi': hr, 'sp': sp, 'boosts': boosts_h,
                         'afflictions': aff_h, 'onlyNodes': only_nodes, 'rkLoss': rk_loss}

    analysis['_houses']  = houses
    analysis['_mepDeg']  = mep_deg
    analysis['_sunIsFM'] = sun_is_fm

    # ── Node strength = house strength of occupied sign ──
    for a in analysis.values():
        if not isinstance(a, dict) or 'graha' not in a or not a['isNode']:
            continue
        h = houses.get(a['house'])
        if not h:
            continue
        if h['mt']:
            la = analysis.get(h['lord'])
            ns = la['strengthPct'] if isinstance(la, dict) else 1.0
        else:
            ns = min(h['sp'], 1.0)
        a['strengthPct'] = ns
        a['isWeak']      = ns < 0.60

    return analysis


# ─── screen_muhurta ────────────────────────────────────────────────────────

def screen_muhurta(data: dict, analysis: dict, cfg: dict) -> dict:
    """Screens a chart against muhurta rules. Returns {pass, ...} with exceptionsUsed list."""
    lr  = data['lagna']['rashi']
    fms = FUNC_MALEFICS.get(lr, set())
    mep_deg = data['lagna']['degree_in_rashi']
    lagna_ruler = LAGNA_RULER.get(lr)
    exceptions_used: list[str] = []

    fm_data = []
    for g in data['grahas']:
        if g['graha'] in ('Rahu', 'Ketu') or g['graha'] in fms:
            house = ((g['rashi'] - lr + 12) % 12) + 1
            fm_data.append({'graha': g['graha'], 'house': house,
                            'deg': g['degree_in_rashi'], 'rashi': g['rashi']})

    # Rule 3b: per-planet minimum strength
    # Lagna lord minimum comes from cfg['lagnaLordMin'] (default 60%, Any=0 means unchecked).
    # Per-planet filter can raise individual planet minimums higher.
    planet_mins   = cfg.get('planetMins', {})
    lagna_lord_mn = float(cfg.get('lagnaLordMin', 0.60) or 0)
    for p in MUHURTA_PLANETS:
        mn = float(planet_mins.get(p, 0) or 0)
        if p == lagna_ruler:
            mn = max(lagna_lord_mn, mn)
            if mn > 0:
                pa = analysis.get(p)
                if isinstance(pa, dict) and pa.get('strengthPct', 1.0) < mn:
                    pct = round(pa['strengthPct'] * 100)
                    return {'pass': False,
                            'reason': f'Lagna lord {p} strength {pct}% < {round(mn*100)}% required'}
            continue  # lagna lord already checked above
        if mn > 0:
            pa = analysis.get(p)
            if isinstance(pa, dict) and pa.get('strengthPct', 1.0) < mn:
                pct = round(pa['strengthPct'] * 100)
                return {'pass': False,
                        'reason': f'{p} strength {pct}% < {round(mn*100)}% required'}

    # Rule 4: any planet in dushtana
    planet_entries = [a for a in analysis.values() if isinstance(a, dict) and 'graha' in a]
    for a in planet_entries:
        if a['inDushtana']:
            return {'pass': False, 'reason': f"{a['graha']} badly placed (h{a['house']})"}

    # Rule 5a: special afflictions — each type can be individually allowed as exception
    # Types: isRaKe, isMmp, fmInDust, chainSpecial, cond5
    for a in planet_entries:
        for asp in a['allFmAspects']:
            if not ((asp['special'] or asp['chainSpecial']) and asp['isDamaging']):
                continue
            aff_label = 'Ra-Ke' if asp.get('isRaKe') else asp['fm']
            allowed = False
            if asp.get('isRaKe')      and cfg.get('allowAffRaKe'):   allowed = True
            if asp.get('isMmp')       and cfg.get('allowAffMmp'):    allowed = True
            if asp.get('fmInDust')    and cfg.get('allowAffDust'):   allowed = True
            if asp.get('chainSpecial') and cfg.get('allowAffChain'): allowed = True
            if asp.get('cond5')       and cfg.get('allowAffCond5'):  allowed = True
            if allowed:
                exceptions_used.append(f'Aff {aff_label}→{a["graha"]}')
                continue
            return {'pass': False, 'reason': f"Special affliction: {aff_label} on {a['graha']}"}

    # Rule 5b: 2+ FMs afflict MEP of same MT sign house
    for h in range(1, 13):
        hr = ((lr - 1 + h - 1) % 12) + 1
        if not MOOLA_LORD.get(hr):
            continue
        seen: set[str] = set()
        for fm in fm_data:
            if mep_orb(fm['graha'], fm['house'], fm['deg'], fm['rashi'], h, mep_deg, lr) < 5:
                seen.add(fm['graha'])
        if len(seen) >= 2:
            if cfg.get('allowRule5b'):
                exceptions_used.append(f'2+ FMs on h{h} MEP ({", ".join(sorted(seen))})')
            else:
                return {'pass': False, 'reason': f'2+ FMs afflict MT house {h} MEP'}

    # Rule 5c: 1 FM afflicts MT sign house MEP AND that house's lord is also afflicted
    def p_aff(planet: str) -> bool:
        a = analysis.get(planet)
        return bool(isinstance(a, dict) and a.get('allFmAspects'))

    for h in range(1, 13):
        hr    = ((lr - 1 + h - 1) % 12) + 1
        hlord = MOOLA_LORD.get(hr)
        if not hlord:
            continue
        h_aff = False
        for fm in fm_data:
            if mep_orb(fm['graha'], fm['house'], fm['deg'], fm['rashi'], h, mep_deg, lr) < 5:
                h_aff = True; break
        if h_aff and p_aff(hlord):
            if cfg.get('allowRule5c'):
                exceptions_used.append(f'FM on h{h} MEP + {hlord} afflicted')
            else:
                return {'pass': False, 'reason': f'FM afflicts h{h} MEP and {hlord} is afflicted'}

    # Rule 5d: No FM within orb of Lagna Lord, its MT sign MEP, or house of occupation MEP
    if cfg.get('noFmLagna'):
        orb5d = 5  # matches JS: cfg.noFmLagna ? 5 : (cfg.mepOrb || 5) is always 5 in this branch

        # Point 1: FM within orb of Lagna Lord's own degree
        ll_an = analysis.get(lagna_ruler)
        if isinstance(ll_an, dict):
            for asp in (ll_an.get('allFmAspects') or []):
                if asp['orb'] < orb5d:
                    return {'pass': False,
                            'reason': f"FM {asp['fm']} within {asp['orb']:.1f}° of Lagna Lord {lagna_ruler}"}

        # Point 2: FM within orb of Lagna Lord's MT sign house MEP
        ll_mt_house = None
        for rashi, lord in MOOLA_LORD.items():
            if lord == lagna_ruler:
                ll_mt_house = ((rashi - lr + 12) % 12) + 1
                break
        if ll_mt_house:
            for fm in fm_data:
                d = mep_orb(fm['graha'], fm['house'], fm['deg'], fm['rashi'], ll_mt_house, mep_deg, lr)
                if d < orb5d:
                    return {'pass': False,
                            'reason': f"FM {fm['graha']} aspects Lagna Lord MT sign (h{ll_mt_house}) MEP within {d:.1f}°"}

        # Point 3: FM within orb of house occupied by Lagna Lord
        ll_graha = next((g for g in data['grahas'] if g['graha'] == lagna_ruler), None)
        if ll_graha:
            ll_house = ((ll_graha['rashi'] - lr + 12) % 12) + 1
            for fm in fm_data:
                d = mep_orb(fm['graha'], fm['house'], fm['deg'], fm['rashi'], ll_house, mep_deg, lr)
                if d < orb5d:
                    return {'pass': False,
                            'reason': f"FM {fm['graha']} aspects Lagna Lord house (h{ll_house}) MEP within {d:.1f}°"}

    # Rule 6: active antardasha
    chart_dt = datetime.fromisoformat(data['birth_data']['date'] + 'T' + data['birth_data']['time'])
    active_antar = None
    for d in (data.get('dasha') or []):
        if active_antar:
            break
        for ad in (d.get('antardasha') or []):
            s = datetime.fromisoformat(ad['start'])
            e = datetime.fromisoformat(ad['end'])
            if s <= chart_dt < e:
                active_antar = {'dasha': d['lord'], 'antar': ad['lord'], 'start': ad['start']}
                break

    if active_antar:
        al = active_antar['antar']
        if al in ('Rahu', 'Ketu'):
            return {'pass': False, 'reason': f'Active antardasha {al} is a node'}
        if al in fms:
            return {'pass': False, 'reason': f'Active antardasha {al} is FM'}
        aa = analysis.get(al)
        antar_min = float(cfg.get('antarMin', 0.70))   # 0 = Any
        if isinstance(aa, dict):
            pct = aa.get('strengthPct', 1.0)
            if antar_min > 0 and pct < antar_min:
                return {'pass': False,
                        'reason': f'Antardasha {al} strength {round(pct*100)}% < {round(antar_min*100)}% required'}
            if pct < 0.70 and (antar_min == 0 or antar_min < 0.70):
                exceptions_used.append(f'Weak antar {al} ({round(pct*100)}%)')
        if isinstance(aa, dict) and aa.get('inDushtana'):
            return {'pass': False,
                    'reason': f'Active antardasha {al} badly placed (h{aa["house"]})'}

    # Benefic window
    benefic_days = None
    if active_antar:
        past_current = False
        for d in (data.get('dasha') or []):
            if benefic_days is not None:
                break
            for ad in (d.get('antardasha') or []):
                if not past_current:
                    s = datetime.fromisoformat(ad['start'])
                    e = datetime.fromisoformat(ad['end'])
                    if s <= chart_dt < e:
                        past_current = True
                        continue
                    if not past_current:
                        continue
                if ad['lord'] in ('Rahu', 'Ketu') or ad['lord'] in fms:
                    mday  = datetime.fromisoformat(data['birth_data']['date'] + 'T00:00:00')
                    malday = datetime.fromisoformat(ad['start'][:10] + 'T00:00:00')
                    benefic_days = round((malday - mday).days)
                    break

    # Q1: Moon nakshatra lord must be FB
    moon_g = next((g for g in data['grahas'] if g['graha'] == 'Moon'), None)
    if not moon_g:
        return {'pass': False, 'reason': 'No Moon data'}
    moon_lon = (moon_g['rashi'] - 1) * 30 + moon_g['degree_in_rashi']
    nak_idx  = int(moon_lon / (360 / 27))
    nak_lord = NAK_LORDS_27[min(nak_idx, 26)]
    if nak_lord in ('Rahu', 'Ketu') or nak_lord in fms:
        return {'pass': False, 'reason': f'Moon nak lord {nak_lord} is FM/node'}

    # Q2: 2+ strong planets
    main_7 = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']
    s_thresh = 0.60 if cfg.get('lowerStrongThreshold') else 0.70
    strong_planets = sum(1 for p in main_7
                        if isinstance(analysis.get(p), dict)
                        and analysis[p].get('strengthPct', 0) >= s_thresh)
    min_sp = cfg.get('minStrongPlanets', 2)
    if strong_planets < min_sp:
        return {'pass': False, 'reason': f'Only {strong_planets} strong planets (need {min_sp}+)'}
    if cfg.get('lowerStrongThreshold'):
        strong_70 = sum(1 for p in main_7
                       if isinstance(analysis.get(p), dict)
                       and analysis[p].get('strengthPct', 0) >= 0.70)
        if strong_70 < min_sp:
            exceptions_used.append(f'Low-strength planets counted ({strong_planets} ≥60%)')

    # Q3: 5+ strong houses
    house_map = analysis.get('_houses', {})
    strong_houses = 0
    for h in range(1, 13):
        hs = house_map.get(h)
        if not hs:
            continue
        if hs['mt']:
            la = analysis.get(hs['lord'])
            sp = la.get('strengthPct', 0) if isinstance(la, dict) else 0
        else:
            sp = hs.get('sp', 0)
        if sp >= s_thresh:
            strong_houses += 1
    min_sh = cfg.get('minStrongHouses', 5)
    if strong_houses < min_sh:
        return {'pass': False, 'reason': f'Only {strong_houses} strong houses (need {min_sh}+)'}
    if cfg.get('lowerStrongThreshold'):
        sh_70 = 0
        for h in range(1, 13):
            hs = house_map.get(h)
            if not hs: continue
            sp = ((analysis.get(hs['lord']) or {}).get('strengthPct', 0)
                  if hs['mt'] else hs.get('sp', 0))
            if sp >= 0.70: sh_70 += 1
        if sh_70 < min_sh and not any('Low-strength' in e for e in exceptions_used):
            exceptions_used.append(f'Low-strength houses counted ({strong_houses} ≥60%)')

    # Benefic window filter
    min_bd = cfg.get('minBeneficDays', 0) or 0
    if min_bd > 0 and (benefic_days is None or benefic_days < min_bd):
        return {'pass': False,
                'reason': f'Benefic window {benefic_days or 0}d < {min_bd}d minimum'}

    antar_str = (active_antar['dasha'] + '/' + active_antar['antar']) if active_antar else '?'
    return {
        'pass': True,
        'strongPlanets':  strong_planets,
        'strongHouses':   strong_houses,
        'antarDasha':     antar_str,
        'antarStart':     active_antar['start'] if active_antar else None,
        'beneficDays':    benefic_days,
        'exceptionsUsed': exceptions_used,
    }
