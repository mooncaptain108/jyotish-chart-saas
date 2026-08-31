# Jyotish Query

Each planet's strength is calculated as a percentage (0%–100%+). The following states are evaluated in sequence — reductions multiply together, so a combust and debilitated planet is weaker than either condition alone.

### Degree-Based Strength (Infancy and Old Age)

Every planet has a degree within its sign (0°–30°). The middle range, 5°–25°, is full strength. Outside that range the planet is in infancy (early degrees) or old age (late degrees) and its strength is reduced proportionally.

- **5°–25°:** Full strength — 100%
- **0°–5° (infancy):** Strength scales from 0% at 0° up to 100% at 5°
- **25°–30° (old age):** Strength scales from 100% at 25° down to 0° at 30°

Lunar nodes (Rahu and Ketu) are not subject to degree-based strength — they are assessed differently.

### Combustion

A planet within close proximity to the Sun is **combust** and loses strength. The orb of combustion varies by planet:
<style>
th {
  color: black;
  background-color: white;
}
table {
  margin-left: 4em;
  border-collapse: collapse;
  width: 40%%;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
</style>

| Planet | Orb |
|-|-|
|Moon |12° |
|Mercury |14° |
|Mars |17° |
|Jupiter |11° |
|Venus |12° |
|Saturn |16° |

- **Combust (Sun is benefic):** ×0.50 — loss of 50%
- **Combust (Sun is functional malefic):** ×0.25 — loss of 75%

Rahu and Ketu cannot be combust.

### Debilitation

A planet in its sign of debilitation (natal chart) is significantly weakened.

- **Debilitated in natal chart only:** ×0.50 — loss of 50%
- **Debilitated in both natal and Navamsa (D9):** ×0.25 — loss of 75%

### Dushtana Placement (Houses 6, 8, 12)

A planet placed in house 6, 8, or 12 is weakened by its bad placement — unless it is in its own Moolatrikona sign in that house, in which case the placement is considered good and no reduction is applied.

- **In dushtana only:** ×0.50 — loss of 50%
- **In dushtana and D9 debilitated:** ×0.40 — loss of 60%

### D9 (Navamsa) Debilitation Alone

When a planet is not debilitated or in a dushtana in the natal chart, but is debilitated in the Navamsa:

- **D9 debilitated only:** ×0.75 — loss of 25%

### Exaltation

A planet in its sign of exaltation gains strength.

- **Exalted in natal chart:** ×1.25 — gain of 25%
- **Exalted in D9 (Navamsa):** ×1.25 — gain of 25%, unless the planet is in a dushtana in the D9

Both boosts can apply if the planet is exalted in both charts.

### Strength Thresholds and Color Coding

After all states, afflictions, and increases are applied:

| Strength | Classification | Color |
|----------|---------------|-------|
| Combust (any %) | Combust | Blue |
| < 60% | Weak | Brown |
| 60%–69% | Middling | Gold |
| ≥ 70% | Strong | Green |

A functional malefic planet is always shown in red regardless of its strength percentage.

---

## Sun-Like Planet Rules

The 2nd, 3rd, and 9th houses are **sun-like houses**. Leo (sign 5) is always sun-like regardless of which house it occupies.

A planet is a **sun-like planet** for a given chart if its Moolatrikona sign falls in house 2, 3, or 9. The Sun itself is always excluded from this designation, confirmed against the primary sources (yournetastrologer.com and Choudhry's "Impact of Rising Signs"): for Gemini, Cancer, and Sagittarius rising — the three lagnas where Leo (Sun's own Moolatrikona sign) falls into a sun-like house (3rd, 2nd, and 9th respectively) — that material lists the other sun-like planet(s) for the chart but never the Sun. The Sun's own strength is instead covered by its own-MT-sign and sun-like-house boosts below, based on where Sun actually sits, not by treating Sun as a proxy "sun-like" planet for a house it merely disposits.

Four boosts apply independently and **stack**:

| Condition | Boost | Suppressible by MEP affliction? |
|---|---|---|
| Planet is a sun-like planet for this chart | +25% | No — inherent to the planet's nature |
| Planet in its own Moolatrikona sign (any house) | +25% | Only if the planet is itself a functional malefic |
| Planet in house 2, 3, or 9 (any sign) | +25% | Only if the planet is itself a functional malefic |
| Planet in Leo (any house, excluding Sun) | +25% | Only if the planet is itself a functional malefic |

The Sun is excluded from the Leo boost because Leo is already Sun's own Moolatrikona sign — applying both would double-count the same condition. Sun in Leo receives only the own MT sign boost (and the sun-like house boost if applicable).

All four conditions are evaluated independently — a planet satisfying more than one receives multiple boosts stacked together.

These increases stack with exaltation and D9 exaltation increases.

**Suppression:** This applies only to a functional malefic's own placement-based boosts. If the planet is a functional malefic and any functional malefic is within **1° of the MEP** of its occupied house, its three placement-based boosts (own MT sign, sun-like house, Leo) are suppressed. Benefic (non-FM) planets are never suppressed by this rule, even when an FM afflicts the MEP of the house they occupy — the affliction still costs them strength through the normal occupied-house affliction loss, just not through this boost-suppression path. The sun-like planet boost is never suppressed for anyone.

**Exception to suppression:** A functional malefic planet placed in its **own Moolatrikona sign** retains all sun-like boosts regardless of MEP proximity. It is still dignified by occupying its own sign, and it still casts its normal aspects to other houses.

**Weak-planet recovery:** A planet receiving a sun-like boost can recover from weakness due to infancy or old age, up to a maximum of 100%.

---

## Functional Benefic Aspect and Conjunction Rules

A **functional benefic (FB)** is any planet that is not a functional malefic and not a lunar node (Rahu/Ketu). When a FB aspects or is conjunct another planet, it can increase that planet's strength.

**increase formula:**
- **Strong FB (≥ 70%):** +50% × (1 − orb / 5), effective up to 5°
- **Weak FB (< 70%):** +12.5% × (1 − orb), only effective within 1°

increases are calculated using each planet's **pre-increase strength** to avoid circular dependencies. All base strengths are evaluated first; then all FB increases are applied in a single pass.

Lunar nodes (Rahu/Ketu) and functional malefic planets never provide benefic increases.

A FB aspect that falls outside its effective range but within 5° is recorded as **(noted)** in the Analysis popover — it is informational only and does not affect strength.

---

## Regular Affliction Rules

An **affliction** occurs when a Functional Malefic (FM) conjuncts or aspects a planet within its effective orb.

Every planet casts a **7th house (180°) aspect**. Additionally:
- Mars aspects the **4th, 7th, and 8th** houses
- Jupiter aspects the **5th, 7th, and 9th** houses
- Saturn aspects the **3rd, 7th, and 10th** houses
- Rahu and Ketu aspect the **5th, 7th, and 9th** houses

**Orb of affliction:**
- **Strong planet (≥ 70%):** only regular afflictions within **1°** are weakening
- **Weak planet (< 70%):** regular afflictions within **5°** are weakening

**Strength loss:**
- Strong planet: flat **−50%** loss (within 1°)
- Weak planet: graduated **−75% × (1 − orb / 5)** — full loss at 0°, tapering to 0 at 5°

---

## Special Affliction Rules

An affliction is **special** when any of the following conditions apply:

1. **Most Malefic Planet (MMP):** The FM is the designated most malefic planet for the rising sign.
2. **Ra-Ke axis conjunction:** Rahu or Ketu is conjunct (same house as) the planet.
3. **FM in dushtana:** The FM is placed in house 6, 8, or 12 and aspects the planet from there.
4. **Chain:** The afflicting FM is itself conjunct or aspected within 5° by another FM.
5. **Multiple FMs:** Two or more FMs (not Ra-Ke see rule 2.) aspect or conjunct within 5° of the planet. For example an aspect of Rahu or Ketu and and aspect or conjuction of another malefic each within 5°.

**Orb of special affliction:**
- **Strong planet:** special affliction within **2°** is weakening
- **Weak planet:** special affliction within **5°** is weakening

**Strength loss from special affliction:**
- Strong planet: flat **−50%** loss (within 2°)
- Weak planet: graduated **−75% × (1 − orb / 5)** — full loss at 0°, tapering to 0 at 5°

---

## Rules for MEP Afflictions

Each house has a **Most Effective Point (MEP)** located at the rising degree of the ascendant. Afflictions to the MEP affect house strength and reduce the strength of the house lord.

### MT House MEP Afflictions

A Moolatrikona (MT) house is one where a planet's MT sign is located. When the MEP of an MT house is afflicted by an FM, the MT lord's strength is also reduced.

**Regular FM affliction to MT house MEP:**
- Within 1°: full **75% loss** on the lord
- 1°–5°: graduated, **75% × (1 − (orb − 1) / 4)**

**Special FM affliction to MT house MEP:**
- Within 2°: full **75% loss** on the lord
- 2°–5°: graduated, **75% × (1 − (orb − 2) / 3)**

Special FM classification uses the same criteria as for direct planet afflictions (MMP, Ra-Ke conjunction, FM-in-dushtana, chain-special, multiple).

### Occupied House MEP Afflictions

When a planet's occupied house MEP is afflicted by an FM, the planet itself takes a loss using the same regular/special graduated formula above.

### Non-MT House Strengths

Houses that are not MT houses start at **100% strength**. Benefic and malefic influences to the MEP adjust this:

| Influence | Formula |
|-----------|---------|
| Strong FB (≥ 70%) | +50% × (1 − orb / 5), up to 5° |
| Weak FB (< 70%) | +12.5% × (1 − orb), only within 1° |
| Regular FM | −50% × (1 − orb / 5), up to 5° |
| Special FM (MMP / Ra-Ke / FM-in-dushtana) | −75% × (1 − orb / 5), up to 5° |

### Dispositor Cap

After all afflictions and increases are applied, a planet's strength can never exceed its **dispositor's** (the lord of the moolatrikona sign it occupies) strength — the dispositor is always a ceiling, whether or not the dispositor is itself weak. This rule cascades — if the dispositor's own dispositor is weaker still, the cap propagates up the chain.

Separately, if the dispositor is **weak**, the disposed planet is also marked weak (not just capped in value) — this is the "occupies the moolatrikona sign of a weak planet" rule. A planet disposed by a strong-but-lower dispositor gets capped to that lower value but is not itself flagged weak on that basis alone.
